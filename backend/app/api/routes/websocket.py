from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.mqqt_service import manager
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    
    try:
        # Jangan panggil websocket.accept() karena manager.connect() sudah memanggil
        # method accept() di dalam implementasinya
        await manager.connect(websocket)
        logger.info("Client WebSocket berhasil terhubung")
        
        # Tunggu pesan masuk dari WebSocket
        # Ini menunggu sampai koneksi terputus atau terjadi error
        while True:
            try:
                # Terima pesan dari client WebSocket
                data = await websocket.receive_text()
                logger.info(f"Menerima pesan dari client WebSocket: {data}")
                
                # Proses pesan jika diperlukan
                try:
                    msg_data = json.loads(data)
                    # Tambahkan logika pemrosesan pesan jika diperlukan
                    
                    # Contoh - kirim respons kembali ke client
                    await websocket.send_text(json.dumps({"status": "received", "message": "Pesan diterima"}))
                    
                except json.JSONDecodeError:
                    logger.warning("Pesan bukan JSON valid")
                    await websocket.send_text(json.dumps({"status": "error", "message": "Format pesan tidak valid"}))
                
            except Exception as e:
                # Jika ada error selain WebSocketDisconnect, masih coba lanjutkan
                if isinstance(e, WebSocketDisconnect):
                    raise  # Re-raise WebSocketDisconnect untuk ditangkap di luar
                logger.error(f"Error menerima pesan: {e}")
    
    except WebSocketDisconnect:
        # Client terputus - hapus dari daftar koneksi aktif
        manager.disconnect(websocket)
        logger.info("Client WebSocket terputus")
    
    except Exception as e:
        # Tangani semua jenis error lainnya
        logger.error(f"Error dalam koneksi WebSocket: {e}")
        # Pastikan koneksi dihapus dari manager
        manager.disconnect(websocket)