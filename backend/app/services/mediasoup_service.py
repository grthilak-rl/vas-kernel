"""
MediaSoup Worker Service

Handles SFU-based WebRTC routing for video streams.
"""
import os
from typing import Dict, Optional, Any
from loguru import logger


class MediaSoupWorker:
    """
    MediaSoup Worker for handling WebRTC SFU operations.
    
    This service will manage:
    - Router creation and management
    - WebRTC transport setup
    - Producer/consumer management
    - RTP transport for FFmpeg forwarding
    """
    
    def __init__(self):
        """Initialize MediaSoup Worker."""
        self.routers: Dict[str, Any] = {}
        self.producers: Dict[str, Any] = {}
        self.consumers: Dict[str, Any] = {}
        self.transports: Dict[str, Any] = {}
        
        logger.info("MediaSoup Worker initialized")
    
    async def create_router(self, router_id: str) -> Dict[str, Any]:
        """
        Create a new MediaSoup router.
        
        Args:
            router_id: Unique identifier for the router
            
        Returns:
            Router configuration
        """
        if router_id in self.routers:
            logger.warning(f"Router {router_id} already exists")
            return self.routers[router_id]
        
        router = {
            "id": router_id,
            "status": "active",
            "created_at": None  # Will be set by MediaSoup
        }
        
        self.routers[router_id] = router
        logger.info(f"Created router: {router_id}")
        
        return router
    
    async def create_webrtc_transport(
        self,
        router_id: str,
        transport_id: str
    ) -> Dict[str, Any]:
        """
        Create WebRTC transport for a router.
        
        Args:
            router_id: Router identifier
            transport_id: Transport identifier
            
        Returns:
            Transport configuration with ICE parameters
        """
        if router_id not in self.routers:
            raise ValueError(f"Router {router_id} does not exist")
        
        transport = {
            "id": transport_id,
            "router_id": router_id,
            "type": "webrtc",
            "ice_parameters": {
                "usernameFragment": "vas_" + transport_id[:8],
                "password": "vas_password_" + transport_id[:8]
            },
            "ice_candidates": [],
            "dtls_parameters": {
                "role": "auto",
                "fingerprints": []
            },
            "status": "active"
        }
        
        self.transports[transport_id] = transport
        logger.info(f"Created WebRTC transport: {transport_id} for router {router_id}")
        
        return transport
    
    async def create_rtp_transport(
        self,
        router_id: str,
        transport_id: str
    ) -> Dict[str, Any]:
        """
        Create RTP transport for FFmpeg forwarding.
        
        Args:
            router_id: Router identifier
            transport_id: Transport identifier
            
        Returns:
            Transport configuration with RTP parameters
        """
        if router_id not in self.routers:
            raise ValueError(f"Router {router_id} does not exist")
        
        transport = {
            "id": transport_id,
            "router_id": router_id,
            "type": "rtp",
            "rtp_parameters": {
                "ip": "0.0.0.0",
                "port": 40000,  # Configurable
                "rtcp_port": 40001
            },
            "status": "active"
        }
        
        self.transports[transport_id] = transport
        logger.info(f"Created RTP transport: {transport_id} for router {router_id}")
        
        return transport
    
    async def create_producer(
        self,
        transport_id: str,
        producer_id: str,
        rtp_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a producer (video source).
        
        Args:
            transport_id: Transport identifier
            producer_id: Producer identifier
            rtp_parameters: RTP parameters
            
        Returns:
            Producer configuration
        """
        if transport_id not in self.transports:
            raise ValueError(f"Transport {transport_id} does not exist")
        
        producer = {
            "id": producer_id,
            "transport_id": transport_id,
            "rtp_parameters": rtp_parameters,
            "status": "active"
        }
        
        self.producers[producer_id] = producer
        logger.info(f"Created producer: {producer_id}")
        
        return producer
    
    async def create_consumer(
        self,
        producer_id: str,
        consumer_id: str,
        rtp_capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a consumer (video viewer).
        
        Args:
            producer_id: Producer identifier
            consumer_id: Consumer identifier
            rtp_capabilities: RTP capabilities
            
        Returns:
            Consumer configuration
        """
        if producer_id not in self.producers:
            raise ValueError(f"Producer {producer_id} does not exist")
        
        consumer = {
            "id": consumer_id,
            "producer_id": producer_id,
            "rtp_parameters": {},
            "status": "active"
        }
        
        self.consumers[consumer_id] = consumer
        logger.info(f"Created consumer: {consumer_id} for producer {producer_id}")
        
        return consumer
    
    async def close_transport(self, transport_id: str) -> None:
        """
        Close and cleanup a transport.
        
        Args:
            transport_id: Transport identifier
        """
        if transport_id in self.transports:
            del self.transports[transport_id]
            logger.info(f"Closed transport: {transport_id}")
    
    async def close_router(self, router_id: str) -> None:
        """
        Close and cleanup a router.
        
        Args:
            router_id: Router identifier
        """
        # Close all transports for this router
        transports_to_close = [
            tid for tid, transport in self.transports.items()
            if transport.get("router_id") == router_id
        ]
        
        for tid in transports_to_close:
            await self.close_transport(tid)
        
        if router_id in self.routers:
            del self.routers[router_id]
            logger.info(f"Closed router: {router_id}")


# Global MediaSoup worker instance
mediasoup_worker = MediaSoupWorker()


