"""
Image Upload Service (Fixed Version)
Handles image uploads, processing, validation, and storage
"""
import os
import uuid
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps
import aiofiles
import asyncio
from pathlib import Path
import logging
import io

logger = logging.getLogger(__name__)

class ImageService:
    """Service for handling image uploads and processing"""
    
    def __init__(self):
        # Supported image formats
        self.allowed_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
        # File size limits (in bytes)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_image_size = 5 * 1024 * 1024   # 5MB for processed images
        
        # Image dimensions
        self.max_width = 4096
        self.max_height = 4096
        self.thumbnail_size = (300, 300)
        self.medium_size = (800, 800)
        
        # Quality settings
        self.jpeg_quality = 85
        self.png_compression = 6
        
        # Storage paths
        self.upload_dir = Path("uploads")
        self.originals_dir = self.upload_dir / "originals"
        self.thumbnails_dir = self.upload_dir / "thumbnails"
        self.medium_dir = self.upload_dir / "medium"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create upload directories if they don't exist"""
        for directory in [self.upload_dir, self.originals_dir, self.thumbnails_dir, self.medium_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_formats:
            validation_result["valid"] = False
            validation_result["errors"].append(f"File format {file_ext} not allowed. Allowed formats: {', '.join(self.allowed_formats)}")
        
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            validation_result["valid"] = False
            validation_result["errors"].append(f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB")
        
        return validation_result
    
    async def _save_file(self, file_content: bytes, file_path: Path) -> bool:
        """Save file content to disk"""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            return True
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return False
    
    def _process_image(self, image: Image.Image, target_size: tuple = None, quality: int = None) -> Image.Image:
        """Process image (resize, optimize, rotate)"""
        # Auto-rotate based on EXIF
        image = ImageOps.exif_transpose(image)
        
        # Convert to RGB if necessary (for JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if target size specified
        if target_size:
            image = ImageOps.contain(image, target_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create thumbnail from image"""
        return self._process_image(image, self.thumbnail_size)
    
    def _create_medium(self, image: Image.Image) -> Image.Image:
        """Create medium-sized image"""
        return self._process_image(image, self.medium_size)
    
    async def upload_image(self, file: UploadFile, user_id: str = None) -> Dict[str, Any]:
        """Upload and process an image"""
        try:
            # Validate file
            validation = self._validate_file(file)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=", ".join(validation["errors"]))
            
            # Read file content
            file_content = await file.read()
            
            # Generate unique filename
            file_hash = self._get_file_hash(file_content)
            file_ext = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Open image for processing
            try:
                image = Image.open(io.BytesIO(file_content))
                image_format = image.format or 'JPEG'
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
            
            # Check image dimensions
            if image.width > self.max_width or image.height > self.max_height:
                validation["warnings"].append(f"Image dimensions ({image.width}x{image.height}) exceed maximum ({self.max_width}x{self.max_height}). Image will be resized.")
            
            # Process images
            original_image = self._process_image(image)
            thumbnail_image = self._create_thumbnail(image)
            medium_image = self._create_medium(image)
            
            # Generate file paths
            original_path = self.originals_dir / unique_filename
            thumbnail_path = self.thumbnails_dir / unique_filename
            medium_path = self.medium_dir / unique_filename
            
            # Save processed images
            await self._save_image(original_image, original_path, image_format)
            await self._save_image(thumbnail_image, thumbnail_path, image_format)
            await self._save_image(medium_image, medium_path, image_format)
            
            # Generate URLs
            base_url = "/uploads"
            result = {
                "success": True,
                "image_id": unique_filename,
                "original_filename": file.filename,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "dimensions": {
                    "original": (original_image.width, original_image.height),
                    "thumbnail": (thumbnail_image.width, thumbnail_image.height),
                    "medium": (medium_image.width, medium_image.height)
                },
                "urls": {
                    "original": f"{base_url}/originals/{unique_filename}",
                    "thumbnail": f"{base_url}/thumbnails/{unique_filename}",
                    "medium": f"{base_url}/medium/{unique_filename}"
                },
                "uploaded_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "warnings": validation["warnings"]
            }
            
            logger.info(f"Image uploaded successfully: {unique_filename}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            raise HTTPException(status_code=500, detail="Image upload failed")
    
    async def _save_image(self, image: Image.Image, file_path: Path, format: str = 'JPEG'):
        """Save processed image to disk"""
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with appropriate format and quality
        if format.upper() == 'PNG':
            image.save(file_path, format='PNG', compress_level=self.png_compression, optimize=True)
        else:
            image.save(file_path, format='JPEG', quality=self.jpeg_quality, optimize=True)
    
    async def delete_image(self, image_id: str) -> bool:
        """Delete an image and all its processed versions"""
        try:
            # Find and delete all versions
            paths_to_delete = [
                self.originals_dir / image_id,
                self.thumbnails_dir / image_id,
                self.medium_dir / image_id
            ]
            
            deleted_count = 0
            for path in paths_to_delete:
                if path.exists():
                    path.unlink()
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} image files for {image_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            return False
    
    async def get_image_info(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an uploaded image"""
        try:
            original_path = self.originals_dir / image_id
            
            if not original_path.exists():
                return None
            
            # Get file info
            stat = original_path.stat()
            
            # Try to get image dimensions
            try:
                with Image.open(original_path) as img:
                    dimensions = (img.width, img.height)
                    format = img.format
            except:
                dimensions = (0, 0)
                format = 'unknown'
            
            return {
                "image_id": image_id,
                "file_size": stat.st_size,
                "dimensions": dimensions,
                "format": format,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "urls": {
                    "original": f"/uploads/originals/{image_id}",
                    "thumbnail": f"/uploads/thumbnails/{image_id}",
                    "medium": f"/uploads/medium/{image_id}"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info for {image_id}: {e}")
            return None
    
    async def list_images(self, user_id: str = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List uploaded images"""
        try:
            images = []
            
            # Get all files in originals directory
            for file_path in self.originals_dir.glob("*"):
                if file_path.is_file():
                    image_info = await self.get_image_info(file_path.name)
                    if image_info and (not user_id or image_info.get("user_id") == user_id):
                        images.append(image_info)
            
            # Sort by creation time (newest first)
            images.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            return images[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage by removing unused files"""
        try:
            stats = {
                "originals_removed": 0,
                "thumbnails_removed": 0,
                "medium_removed": 0,
                "space_freed": 0
            }
            
            # Check for orphaned files (no corresponding original)
            for thumbnail_path in self.thumbnails_dir.glob("*"):
                original_path = self.originals_dir / thumbnail_path.name
                if not original_path.exists():
                    size = thumbnail_path.stat().st_size
                    thumbnail_path.unlink()
                    stats["thumbnails_removed"] += 1
                    stats["space_freed"] += size
            
            for medium_path in self.medium_dir.glob("*"):
                original_path = self.originals_dir / medium_path.name
                if not original_path.exists():
                    size = medium_path.stat().st_size
                    medium_path.unlink()
                    stats["medium_removed"] += 1
                    stats["space_freed"] += size
            
            logger.info(f"Storage optimization completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
            return {"error": str(e)}
    
    def _get_current_time(self) -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat()

# Global instance
image_service = ImageService()
