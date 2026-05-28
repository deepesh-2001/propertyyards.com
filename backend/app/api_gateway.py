"""
API Gateway
Routes requests to appropriate microservices
"""
import aiohttp
import logging
from typing import Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class APIGateway:
    """Routes API calls to microservices"""

    def __init__(self):
        self.services = {
            "flight-price": "http://flight-price-service:80",
            "price-comparison": "http://price-comparison-service:80",
        }
        self.timeout = 30  # seconds

    async def forward_request(
        self,
        service_name: str,
        path: str,
        method: str = "GET",
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> dict:
        """Forward request to microservice"""

        if service_name not in self.services:
            raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

        base_url = self.services[service_name]
        url = f"{base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:

                    if response.status >= 400:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Microservice error: {error_text}"
                        )

                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"Service connection error: {e}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {service_name}")
        except Exception as e:
            logger.error(f"Gateway error: {e}")
            raise HTTPException(status_code=500, detail="Gateway error")

    async def health_check(self, service_name: str) -> dict:
        """Check microservice health"""
        try:
            return await self.forward_request(service_name, "/health")
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global gateway instance
api_gateway = APIGateway()
