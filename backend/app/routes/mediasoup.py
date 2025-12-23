"""
MediaSoup Worker API routes.

Handles MediaSoup operations for WebRTC routing.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.services.mediasoup_service import mediasoup_worker
from loguru import logger

router = APIRouter(prefix="/api/v1/mediasoup", tags=["mediasoup"])


@router.post("/router")
async def create_router(router_id: str) -> Dict[str, Any]:
    """Create a new MediaSoup router."""
    try:
        router_config = await mediasoup_worker.create_router(router_id)
        return {"status": "success", "router": router_config}
    except Exception as e:
        logger.error(f"Failed to create router: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/router/{router_id}/webrtc-transport")
async def create_webrtc_transport(
    router_id: str,
    transport_id: str
) -> Dict[str, Any]:
    """Create WebRTC transport for a router."""
    try:
        transport_config = await mediasoup_worker.create_webrtc_transport(
            router_id, transport_id
        )
        return {"status": "success", "transport": transport_config}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create WebRTC transport: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/router/{router_id}/rtp-transport")
async def create_rtp_transport(
    router_id: str,
    transport_id: str
) -> Dict[str, Any]:
    """Create RTP transport for FFmpeg forwarding."""
    try:
        transport_config = await mediasoup_worker.create_rtp_transport(
            router_id, transport_id
        )
        return {"status": "success", "transport": transport_config}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create RTP transport: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/transport/{transport_id}/producer")
async def create_producer(
    transport_id: str,
    producer_id: str,
    rtp_parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a producer (video source)."""
    try:
        producer_config = await mediasoup_worker.create_producer(
            transport_id, producer_id, rtp_parameters
        )
        return {"status": "success", "producer": producer_config}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create producer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/transport/{transport_id}/consumer")
async def create_consumer(
    producer_id: str,
    consumer_id: str,
    rtp_capabilities: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a consumer (video viewer)."""
    try:
        consumer_config = await mediasoup_worker.create_consumer(
            producer_id, consumer_id, rtp_capabilities
        )
        return {"status": "success", "consumer": consumer_config}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create consumer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/transport/{transport_id}")
async def close_transport(transport_id: str) -> Dict[str, Any]:
    """Close and cleanup a transport."""
    try:
        await mediasoup_worker.close_transport(transport_id)
        return {"status": "success", "message": f"Transport {transport_id} closed"}
    except Exception as e:
        logger.error(f"Failed to close transport: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/router/{router_id}")
async def close_router(router_id: str) -> Dict[str, Any]:
    """Close and cleanup a router."""
    try:
        await mediasoup_worker.close_router(router_id)
        return {"status": "success", "message": f"Router {router_id} closed"}
    except Exception as e:
        logger.error(f"Failed to close router: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


