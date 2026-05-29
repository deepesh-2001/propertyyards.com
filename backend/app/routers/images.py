"""
Image Upload Router
API endpoints for image upload, processing, and management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
from pydantic import BaseModel
import os
from pathlib import Path

from app.database import get_db
from app.auth import get_current_user, require_admin
from app.image_service import image_service
from app.security import SecurityValidator

router = APIRouter(prefix="/api/images", tags=["images"])

# ========== Request Models ==========

class ImageDeleteRequest(BaseModel):
    image_id: str


class ImageInfoResponse(BaseModel):
    image_id: str
    original_filename: str
    file_size: int
    dimensions: dict
    urls: dict
    uploaded_at: str
    user_id: Optional[str] = None


# ========== Upload Endpoints ==========

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload an image with automatic processing and optimization"""
    try:
        # Use current user ID if not provided
        if not user_id:
            user_id = str(current_user.get("_id", "anonymous"))
        
        # Validate file size before processing
        if hasattr(file, 'size') and file.size > image_service.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {image_service.max_file_size // (1024*1024)}MB"
            )
        
        # Upload and process image
        result = await image_service.upload_image(file, user_id)
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple images with batch processing"""
    try:
        # Use current user ID if not provided
        if not user_id:
            user_id = str(current_user.get("_id", "anonymous"))
        
        results = []
        errors = []
        
        for i, file in enumerate(files):
            try:
                result = await image_service.upload_image(file, user_id)
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": True,
                    "data": result
                })
            except Exception as e:
                errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "total_files": len(files),
            "successful_uploads": len(results),
            "failed_uploads": len(errors),
            "results": results,
            "errors": errors,
            "message": f"Uploaded {len(results)} of {len(files)} images successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


# ========== Management Endpoints ==========

@router.get("/list")
async def list_images(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List uploaded images with pagination"""
    try:
        # Users can only see their own images, admins can see all
        if current_user.get("role") != "admin":
            user_id = str(current_user.get("_id"))
        
        images = await image_service.list_images(user_id=user_id, limit=limit, offset=offset)
        
        return {
            "success": True,
            "data": images,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(images)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")


@router.get("/{image_id}")
async def get_image_info(
    image_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific image"""
    try:
        image_info = await image_service.get_image_info(image_id)
        
        if not image_info:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if user has permission to view this image
        if (current_user.get("role") != "admin" and 
            image_info.get("user_id") and 
            image_info.get("user_id") != str(current_user.get("_id"))):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "data": image_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image info: {str(e)}")


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an image and all its processed versions"""
    try:
        # Get image info to check permissions
        image_info = await image_service.get_image_info(image_id)
        
        if not image_info:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check permissions (admin or image owner)
        if (current_user.get("role") != "admin" and 
            image_info.get("user_id") != str(current_user.get("_id"))):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the image
        success = await image_service.delete_image(image_id)
        
        if success:
            return {
                "success": True,
                "message": f"Image {image_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete image")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")


# ========== File Serving Endpoints ==========

@router.get("/files/originals/{image_id}")
async def get_original_image(image_id: str):
    """Serve original image file"""
    try:
        file_path = image_service.originals_dir / image_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(
            path=str(file_path),
            filename=image_id,
            media_type=f"image/{image_id.split('.')[-1].lower()}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")


@router.get("/files/thumbnails/{image_id}")
async def get_thumbnail_image(image_id: str):
    """Serve thumbnail image file"""
    try:
        file_path = image_service.thumbnails_dir / image_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            path=str(file_path),
            filename=f"thumb_{image_id}",
            media_type=f"image/{image_id.split('.')[-1].lower()}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve thumbnail: {str(e)}")


@router.get("/files/medium/{image_id}")
async def get_medium_image(image_id: str):
    """Serve medium-sized image file"""
    try:
        file_path = image_service.medium_dir / image_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Medium image not found")
        
        return FileResponse(
            path=str(file_path),
            filename=f"medium_{image_id}",
            media_type=f"image/{image_id.split('.')[-1].lower()}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve medium image: {str(e)}")


# ========== Admin Endpoints ==========

@router.post("/optimize-storage")
async def optimize_storage(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin())
):
    """Optimize storage by removing orphaned files"""
    try:
        # Run optimization in background
        background_tasks.add_task(image_service.optimize_storage)
        
        return {
            "success": True,
            "message": "Storage optimization started in background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage optimization failed: {str(e)}")


@router.get("/stats")
async def get_storage_stats(
    current_user: dict = Depends(require_admin())
):
    """Get storage statistics and usage information"""
    try:
        # Calculate directory sizes
        def get_dir_size(directory: Path) -> int:
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        
        stats = {
            "storage_usage": {
                "originals": {
                    "size_bytes": get_dir_size(image_service.originals_dir),
                    "size_mb": get_dir_size(image_service.originals_dir) // (1024 * 1024),
                    "file_count": len(list(image_service.originals_dir.glob("*")))
                },
                "thumbnails": {
                    "size_bytes": get_dir_size(image_service.thumbnails_dir),
                    "size_mb": get_dir_size(image_service.thumbnails_dir) // (1024 * 1024),
                    "file_count": len(list(image_service.thumbnails_dir.glob("*")))
                },
                "medium": {
                    "size_bytes": get_dir_size(image_service.medium_dir),
                    "size_mb": get_dir_size(image_service.medium_dir) // (1024 * 1024),
                    "file_count": len(list(image_service.medium_dir.glob("*")))
                },
                "total": {
                    "size_bytes": get_dir_size(image_service.upload_dir),
                    "size_mb": get_dir_size(image_service.upload_dir) // (1024 * 1024)
                }
            },
            "configuration": {
                "max_file_size_mb": image_service.max_file_size // (1024 * 1024),
                "max_image_size_mb": image_service.max_image_size // (1024 * 1024),
                "max_dimensions": f"{image_service.max_width}x{image_service.max_height}",
                "thumbnail_size": f"{image_service.thumbnail_size[0]}x{image_service.thumbnail_size[1]}",
                "medium_size": f"{image_service.medium_size[0]}x{image_service.medium_size[1]}",
                "supported_formats": list(image_service.allowed_formats)
            }
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


# ========== Utility Endpoints ==========

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported image formats and configuration"""
    return {
        "success": True,
        "data": {
            "supported_formats": list(image_service.allowed_formats),
            "max_file_size_mb": image_service.max_file_size // (1024 * 1024),
            "max_dimensions": {
                "width": image_service.max_width,
                "height": image_service.max_height
            },
            "processing_sizes": {
                "thumbnail": image_service.thumbnail_size,
                "medium": image_service.medium_size
            },
            "quality_settings": {
                "jpeg_quality": image_service.jpeg_quality,
                "png_compression": image_service.png_compression
            }
        }
    }


@router.get("/health")
async def image_service_health():
    """Check image service health"""
    try:
        # Check if directories exist and are writable
        checks = {
            "upload_directory": image_service.upload_dir.exists(),
            "originals_directory": image_service.originals_dir.exists(),
            "thumbnails_directory": image_service.thumbnails_dir.exists(),
            "medium_directory": image_service.medium_dir.exists(),
            "disk_space_available": os.statvfs(image_service.upload_dir).f_bavail > 1000
        }
        
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": image_service._get_current_time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": image_service._get_current_time()
        }
