"""
Whiteboard Manager
Handles collaborative whiteboard functionality with items, sharing, and permissions
Optimized with persistent caching and batch operations
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key, invalidate_cache_pattern
from app.persistent_cache import persistent_cache

logger = logging.getLogger(__name__)


class WhiteboardManager:
    """Manager for whiteboard operations"""

    def __init__(self):
        self.cache_prefix = "whiteboard:"
        self.cache_ttl = 300  # 5 minutes

    async def create_whiteboard(
        self,
        whiteboard_data: Dict[str, Any],
        owner_id: str,
        database
    ) -> Dict[str, Any]:
        """Create a new whiteboard"""
        try:
            whiteboard = {
                **whiteboard_data,
                "owner_id": owner_id,
                "items": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await database.whiteboards.insert_one(whiteboard)
            whiteboard["id"] = str(result.inserted_id)

            # Invalidate cache
            await invalidate_cache_pattern(f"{self.cache_prefix}*")

            logger.info(f"Whiteboard created: {whiteboard['id']}")
            return whiteboard

        except Exception as e:
            logger.error(f"Whiteboard creation error: {e}")
            raise

    async def get_whiteboard(
        self,
        whiteboard_id: str,
        user_id: str,
        database
    ) -> Optional[Dict[str, Any]]:
        """Get a whiteboard by ID with permission check"""
        try:
            # Check cache
            cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            whiteboard = await database.whiteboards.find_one({"_id": whiteboard_id})
            if not whiteboard:
                return None

            # Check permission
            if not await self._has_permission(whiteboard_id, user_id, "view", database):
                return None

            # Get items
            cursor = database.whiteboard_items.find({"whiteboard_id": whiteboard_id})
            items = await cursor.to_list(length=1000)

            for item in items:
                item["id"] = str(item["_id"])
                del item["_id"]

            whiteboard["id"] = str(whiteboard["_id"])
            del whiteboard["_id"]
            whiteboard["items"] = items

            # Cache the result
            await set_in_cache(cache_key, whiteboard, ttl=self.cache_ttl)

            return whiteboard

        except Exception as e:
            logger.error(f"Whiteboard retrieval error: {e}")
            return None

    async def update_whiteboard(
        self,
        whiteboard_id: str,
        update_data: Dict[str, Any],
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Update a whiteboard"""
        try:
            # Check permission
            if not await self._has_permission(whiteboard_id, user_id, "edit", database):
                raise ValueError("Permission denied")

            update_data["updated_at"] = datetime.utcnow()

            result = await database.whiteboards.update_one(
                {"_id": whiteboard_id},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("Whiteboard update failed")

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
            await delete_from_cache(cache_key)
            await invalidate_cache_pattern(f"{self.cache_prefix}list:*")

            updated = await self.get_whiteboard(whiteboard_id, user_id, database)
            return updated

        except Exception as e:
            logger.error(f"Whiteboard update error: {e}")
            raise

    async def delete_whiteboard(
        self,
        whiteboard_id: str,
        user_id: str,
        database
    ) -> bool:
        """Delete a whiteboard"""
        try:
            # Check if user is owner
            whiteboard = await database.whiteboards.find_one({"_id": whiteboard_id})
            if not whiteboard:
                return False

            if whiteboard["owner_id"] != user_id:
                raise ValueError("Only owner can delete whiteboard")

            # Delete items
            await database.whiteboard_items.delete_many({"whiteboard_id": whiteboard_id})

            # Delete shares
            await database.whiteboard_shares.delete_many({"whiteboard_id": whiteboard_id})

            # Delete whiteboard
            await database.whiteboards.delete_one({"_id": whiteboard_id})

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
            await delete_from_cache(cache_key)
            await invalidate_cache_pattern(f"{self.cache_prefix}*")

            logger.info(f"Whiteboard deleted: {whiteboard_id}")
            return True

        except Exception as e:
            logger.error(f"Whiteboard deletion error: {e}")
            raise

    async def list_whiteboards(
        self,
        user_id: str,
        is_public: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        database = None
    ) -> List[Dict[str, Any]]:
        """List whiteboards accessible to user"""
        try:
            # Check cache
            cache_key = generate_cache_key(
                self.cache_prefix,
                "list",
                user_id,
                is_public,
                str(tags) if tags else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            # Build query
            query = {
                "$or": [
                    {"owner_id": user_id},
                    {"is_public": True},
                    {"_id": {"$in": await self._get_shared_whiteboard_ids(user_id, database)}}
                ]
            }

            if is_public is not None:
                query["is_public"] = is_public

            if tags:
                query["tags"] = {"$in": tags}

            cursor = database.whiteboards.find(query).sort("updated_at", -1)
            whiteboards = await cursor.to_list(length=100)

            result = []
            for wb in whiteboards:
                # Get item count
                item_count = await database.whiteboard_items.count_documents({"whiteboard_id": wb["_id"]})

                # Get owner name
                owner = await database.users.find_one({"_id": wb["owner_id"]})
                owner_name = owner.get("full_name") or owner.get("username") if owner else None

                result.append({
                    "id": str(wb["_id"]),
                    "title": wb["title"],
                    "description": wb.get("description"),
                    "is_public": wb["is_public"],
                    "owner_id": wb["owner_id"],
                    "owner_name": owner_name,
                    "item_count": item_count,
                    "created_at": wb["created_at"],
                    "updated_at": wb["updated_at"]
                })

            # Cache the result
            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Whiteboard list error: {e}")
            return []

    async def add_item(
        self,
        whiteboard_id: str,
        item_data: Dict[str, Any],
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Add an item to a whiteboard"""
        try:
            # Check permission
            if not await self._has_permission(whiteboard_id, user_id, "edit", database):
                raise ValueError("Permission denied")

            item = {
                **item_data,
                "whiteboard_id": whiteboard_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await database.whiteboard_items.insert_one(item)
            item["id"] = str(result.inserted_id)

            # Update whiteboard timestamp
            await database.whiteboards.update_one(
                {"_id": whiteboard_id},
                {"$set": {"updated_at": datetime.utcnow()}}
            )

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
            await delete_from_cache(cache_key)

            logger.info(f"Whiteboard item added: {item['id']}")
            return item

        except Exception as e:
            logger.error(f"Whiteboard item addition error: {e}")
            raise

    async def update_item(
        self,
        item_id: str,
        update_data: Dict[str, Any],
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Update a whiteboard item"""
        try:
            # Get item to check whiteboard permission
            item = await database.whiteboard_items.find_one({"_id": item_id})
            if not item:
                raise ValueError("Item not found")

            # Check permission
            if not await self._has_permission(item["whiteboard_id"], user_id, "edit", database):
                raise ValueError("Permission denied")

            update_data["updated_at"] = datetime.utcnow()

            result = await database.whiteboard_items.update_one(
                {"_id": item_id},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("Item update failed")

            # Update whiteboard timestamp
            await database.whiteboards.update_one(
                {"_id": item["whiteboard_id"]},
                {"$set": {"updated_at": datetime.utcnow()}}
            )

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, item["whiteboard_id"])
            await delete_from_cache(cache_key)

            updated = await database.whiteboard_items.find_one({"_id": item_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]

            return updated

        except Exception as e:
            logger.error(f"Whiteboard item update error: {e}")
            raise

    async def delete_item(
        self,
        item_id: str,
        user_id: str,
        database
    ) -> bool:
        """Delete a whiteboard item"""
        try:
            # Get item to check whiteboard permission
            item = await database.whiteboard_items.find_one({"_id": item_id})
            if not item:
                return False

            # Check permission
            if not await self._has_permission(item["whiteboard_id"], user_id, "edit", database):
                raise ValueError("Permission denied")

            await database.whiteboard_items.delete_one({"_id": item_id})

            # Update whiteboard timestamp
            await database.whiteboards.update_one(
                {"_id": item["whiteboard_id"]},
                {"$set": {"updated_at": datetime.utcnow()}}
            )

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, item["whiteboard_id"])
            await delete_from_cache(cache_key)

            logger.info(f"Whiteboard item deleted: {item_id}")
            return True

        except Exception as e:
            logger.error(f"Whiteboard item deletion error: {e}")
            raise

    async def share_whiteboard(
        self,
        whiteboard_id: str,
        user_id: str,
        target_user_id: str,
        permission: str,
        shared_by: str,
        database
    ) -> Dict[str, Any]:
        """Share a whiteboard with another user"""
        try:
            # Check if user is owner or admin
            if not await self._has_permission(whiteboard_id, user_id, "admin", database):
                raise ValueError("Only owner or admin can share")

            # Check if already shared
            existing = await database.whiteboard_shares.find_one({
                "whiteboard_id": whiteboard_id,
                "user_id": target_user_id
            })

            if existing:
                # Update permission
                await database.whiteboard_shares.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"permission": permission}}
                )
                share_id = str(existing["_id"])
            else:
                # Create new share
                share = {
                    "whiteboard_id": whiteboard_id,
                    "user_id": target_user_id,
                    "permission": permission,
                    "shared_by": shared_by,
                    "created_at": datetime.utcnow()
                }
                result = await database.whiteboard_shares.insert_one(share)
                share_id = str(result.inserted_id)

            # Invalidate cache
            await invalidate_cache_pattern(f"{self.cache_prefix}*")

            logger.info(f"Whiteboard shared: {whiteboard_id} -> {target_user_id}")
            return {"id": share_id, "whiteboard_id": whiteboard_id, "user_id": target_user_id, "permission": permission}

        except Exception as e:
            logger.error(f"Whiteboard share error: {e}")
            raise

    async def unshare_whiteboard(
        self,
        whiteboard_id: str,
        user_id: str,
        target_user_id: str,
        database
    ) -> bool:
        """Remove share from a whiteboard"""
        try:
            # Check if user is owner or admin
            if not await self._has_permission(whiteboard_id, user_id, "admin", database):
                raise ValueError("Only owner or admin can unshare")

            result = await database.whiteboard_shares.delete_one({
                "whiteboard_id": whiteboard_id,
                "user_id": target_user_id
            })

            # Invalidate cache
            await invalidate_cache_pattern(f"{self.cache_prefix}*")

            logger.info(f"Whiteboard unshared: {whiteboard_id} -> {target_user_id}")
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Whiteboard unshare error: {e}")
            raise

    async def get_shares(
        self,
        whiteboard_id: str,
        user_id: str,
        database
    ) -> List[Dict[str, Any]]:
        """Get all shares for a whiteboard"""
        try:
            # Check permission
            if not await self._has_permission(whiteboard_id, user_id, "view", database):
                raise ValueError("Permission denied")

            cursor = database.whiteboard_shares.find({"whiteboard_id": whiteboard_id})
            shares = await cursor.to_list(length=100)

            result = []
            for share in shares:
                # Get user details
                user = await database.users.find_one({"_id": share["user_id"]})
                user_name = user.get("full_name") or user.get("username") if user else None

                result.append({
                    "id": str(share["_id"]),
                    "whiteboard_id": share["whiteboard_id"],
                    "user_id": share["user_id"],
                    "user_name": user_name,
                    "permission": share["permission"],
                    "shared_by": share["shared_by"],
                    "created_at": share["created_at"]
                })

            return result

        except Exception as e:
            logger.error(f"Whiteboard shares retrieval error: {e}")
            return []

    async def _has_permission(
        self,
        whiteboard_id: str,
        user_id: str,
        required_permission: str,
        database
    ) -> bool:
        """Check if user has required permission for whiteboard"""
        try:
            whiteboard = await database.whiteboards.find_one({"_id": whiteboard_id})
            if not whiteboard:
                return False

            # Owner has all permissions
            if whiteboard["owner_id"] == user_id:
                return True

            # Public whiteboards can be viewed by anyone
            if whiteboard["is_public"] and required_permission == "view":
                return True

            # Check share permissions
            share = await database.whiteboard_shares.find_one({
                "whiteboard_id": whiteboard_id,
                "user_id": user_id
            })

            if not share:
                return False

            permission_hierarchy = {"view": 1, "edit": 2, "admin": 3}
            user_level = permission_hierarchy.get(share["permission"], 0)
            required_level = permission_hierarchy.get(required_permission, 0)

            return user_level >= required_level

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False

    async def _get_shared_whiteboard_ids(
        self,
        user_id: str,
        database
    ) -> List[str]:
        """Get list of whiteboard IDs shared with user"""
        try:
            cursor = database.whiteboard_shares.find({"user_id": user_id})
            shares = await cursor.to_list(length=1000)
            return [s["whiteboard_id"] for s in shares]
        except Exception as e:
            logger.error(f"Shared whiteboards retrieval error: {e}")
            return []

    # ========== Batch Operations ==========

    async def batch_add_items(
        self,
        whiteboard_id: str,
        items_data: List[Dict[str, Any]],
        user_id: str,
        database
    ) -> List[Dict[str, Any]]:
        """Add multiple items to a whiteboard in batch"""
        try:
            # Check permission
            if not await self._has_permission(whiteboard_id, user_id, "edit", database):
                raise ValueError("Permission denied")

            # Prepare items
            items = []
            now = datetime.utcnow()
            for item_data in items_data:
                item = {
                    **item_data,
                    "whiteboard_id": whiteboard_id,
                    "created_at": now,
                    "updated_at": now
                }
                items.append(item)

            # Insert all at once
            result = await database.whiteboard_items.insert_many(items)

            # Update whiteboard timestamp
            await database.whiteboards.update_one(
                {"_id": whiteboard_id},
                {"$set": {"updated_at": now}}
            )

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
            await delete_from_cache(cache_key)

            # Return items with IDs
            for i, item in enumerate(items):
                item["id"] = str(result.inserted_ids[i])

            logger.info(f"Batch added {len(items)} items to whiteboard {whiteboard_id}")
            return items

        except Exception as e:
            logger.error(f"Batch add items error: {e}")
            raise

    async def batch_update_items(
        self,
        updates: List[Dict[str, Any]],
        user_id: str,
        database
    ) -> List[Dict[str, Any]]:
        """Update multiple items in batch"""
        try:
            results = []
            now = datetime.utcnow()

            for update in updates:
                item_id = update["id"]

                # Get item to check permission
                item = await database.whiteboard_items.find_one({"_id": item_id})
                if not item:
                    continue

                # Check permission
                if not await self._has_permission(item["whiteboard_id"], user_id, "edit", database):
                    continue

                # Prepare update
                update_data = {k: v for k, v in update.items() if k != "id"}
                update_data["updated_at"] = now

                await database.whiteboard_items.update_one(
                    {"_id": item_id},
                    {"$set": update_data}
                )

                # Get updated item
                updated = await database.whiteboard_items.find_one({"_id": item_id})
                updated["id"] = str(updated["_id"])
                del updated["_id"]
                results.append(updated)

            # Invalidate caches
            for update in updates:
                if "id" in update:
                    item = await database.whiteboard_items.find_one({"_id": update["id"]})
                    if item:
                        cache_key = generate_cache_key(self.cache_prefix, item["whiteboard_id"])
                        await delete_from_cache(cache_key)

            logger.info(f"Batch updated {len(results)} items")
            return results

        except Exception as e:
            logger.error(f"Batch update items error: {e}")
            raise

    async def batch_delete_items(
        self,
        item_ids: List[str],
        user_id: str,
        database
    ) -> int:
        """Delete multiple items in batch"""
        try:
            deleted_count = 0
            affected_whiteboards = set()

            for item_id in item_ids:
                item = await database.whiteboard_items.find_one({"_id": item_id})
                if not item:
                    continue

                # Check permission
                if not await self._has_permission(item["whiteboard_id"], user_id, "edit", database):
                    continue

                await database.whiteboard_items.delete_one({"_id": item_id})
                affected_whiteboards.add(item["whiteboard_id"])
                deleted_count += 1

            # Update whiteboard timestamps and invalidate caches
            for whiteboard_id in affected_whiteboards:
                await database.whiteboards.update_one(
                    {"_id": whiteboard_id},
                    {"$set": {"updated_at": datetime.utcnow()}}
                )
                cache_key = generate_cache_key(self.cache_prefix, whiteboard_id)
                await delete_from_cache(cache_key)

            logger.info(f"Batch deleted {deleted_count} items")
            return deleted_count

        except Exception as e:
            logger.error(f"Batch delete items error: {e}")
            raise

    async def export_whiteboard(
        self,
        whiteboard_id: str,
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Export whiteboard data for efficient storage/transmission"""
        try:
            whiteboard = await self.get_whiteboard(whiteboard_id, user_id, database)
            if not whiteboard:
                raise ValueError("Whiteboard not found")

            # Compress data
            export = {
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "whiteboard": {
                    "id": whiteboard["id"],
                    "title": whiteboard["title"],
                    "description": whiteboard.get("description"),
                    "background_color": whiteboard["background_color"],
                    "grid_enabled": whiteboard["grid_enabled"],
                    "is_public": whiteboard["is_public"],
                    "tags": whiteboard["tags"],
                    "owner_id": whiteboard["owner_id"]
                },
                "items": [
                    {
                        "id": item["id"],
                        "item_type": item["item_type"],
                        "x": item["x"],
                        "y": item["y"],
                        "width": item.get("width"),
                        "height": item.get("height"),
                        "content": item.get("content"),
                        "color": item.get("color"),
                        "background_color": item.get("background_color"),
                        "font_size": item.get("font_size"),
                        "rotation": item.get("rotation"),
                        "z_index": item.get("z_index"),
                        "metadata": item.get("metadata")
                    }
                    for item in whiteboard.get("items", [])
                ]
            }

            return export

        except Exception as e:
            logger.error(f"Export whiteboard error: {e}")
            raise

    async def import_whiteboard(
        self,
        export_data: Dict[str, Any],
        owner_id: str,
        database
    ) -> Dict[str, Any]:
        """Import whiteboard data"""
        try:
            # Create whiteboard
            whiteboard_data = {
                "title": export_data["whiteboard"]["title"],
                "description": export_data["whiteboard"].get("description"),
                "background_color": export_data["whiteboard"]["background_color"],
                "grid_enabled": export_data["whiteboard"]["grid_enabled"],
                "is_public": export_data["whiteboard"]["is_public"],
                "tags": export_data["whiteboard"]["tags"]
            }

            whiteboard = await self.create_whiteboard(whiteboard_data, owner_id, database)

            # Batch add items
            items_data = [
                {
                    "item_type": item["item_type"],
                    "x": item["x"],
                    "y": item["y"],
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "content": item.get("content"),
                    "color": item.get("color"),
                    "background_color": item.get("background_color"),
                    "font_size": item.get("font_size"),
                    "rotation": item.get("rotation"),
                    "z_index": item.get("z_index"),
                    "metadata": item.get("metadata")
                }
                for item in export_data.get("items", [])
            ]

            if items_data:
                await self.batch_add_items(whiteboard["id"], items_data, owner_id, database)

            # Refresh and return
            return await self.get_whiteboard(whiteboard["id"], owner_id, database)

        except Exception as e:
            logger.error(f"Import whiteboard error: {e}")
            raise


# Global manager instance
whiteboard_manager = WhiteboardManager()
