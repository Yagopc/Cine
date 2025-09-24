#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import signal

class VideoHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.current_player = None
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            url = data.get('url', '')
            print(f"📱 URL recibida: {url}")
            
            # Cerrar reproductor anterior si existe
            self.close_previous_player()
            
            # Headers CORS
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Reproducir nuevo video
            player_used = self.play_video(url)
            
            if player_used:
                response = {'status': 'success', 'player': player_used}
            else:
                response = {'status': 'error', 'message': 'No hay reproductor disponible'}
                
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
    
    def close_previous_player(self):
        """Cierra el reproductor anterior si está activo"""
        if self.current_player and self.current_player.poll() is None:
            print("🔄 Cerrando reproductor anterior...")
            try:
                # Terminar el proceso del reproductor
                self.current_player.terminate()
                self.current_player.wait(timeout=5)
            except:
                try:
                    # Forzar cierre si no responde
                    self.current_player.kill()
                except:
                    pass
            finally:
                self.current_player = None
    
    def play_video(self, url):
        """Reproduce video en pantalla completa"""
        players = [
            {
                'name': 'vlc',
                'command': ['vlc', '--fullscreen', '--play-and-exit', url]
            },
            {
                'name': 'mpv', 
                'command': ['mpv', '--fullscreen', '--force-window=yes', url]
            },
            {
                'name': 'ffplay',
                'command': ['ffplay', '-fs', '-autoexit', url]
            },
            {
                'name': 'celluloid',
                'command': ['celluloid', '--fullscreen', url]
            }
        ]
        
        for player in players:
            try:
                check = subprocess.run(['which', player['name']], capture_output=True)
                if check.returncode == 0:
                    print(f"🎬 Abriendo {player['name']} en pantalla completa...")
                    
                    # Ejecutar en nuevo proceso group para mejor control
                    self.current_player = subprocess.Popen(
                        player['command'],
                        preexec_fn=os.setsid  # Para poder cerrar todo el grupo de procesos
                    )
                    
                    print(f"✅ Reproduciendo con: {player['name']}")
                    return player['name']
                    
            except Exception as e:
                print(f"❌ Error con {player['name']}: {e}")
                continue
        
        return None
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🎬 Servidor de Video Linux</h1>
            <p><strong>Estado:</strong> ✅ Funcionando</p>
            <p><strong>IP:</strong> 192.168.0.11:8080</p>
            <p><strong>Función:</strong> Abre videos en pantalla completa</p>
            <p><strong>Acción:</strong> Cierra automáticamente el video anterior</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

# Manejar señal de cierre para limpiar procesos
import signal
def signal_handler(sig, frame):
    print("\n🛑 Cerrando servidor y limpiando procesos...")
    # Aquí podríamos añadir limpieza global si fuera necesario
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("🚀 Servidor de Video Mejorado Iniciado")
print("📍 URL: http://192.168.0.11:8080")
print("📱 Listo para recibir videos en pantalla completa")
print("🔄 Cierra automáticamente el video anterior")
print("-" * 50)

server = HTTPServer(('0.0.0.0', 8080), VideoHandler)
server.serve_forever()