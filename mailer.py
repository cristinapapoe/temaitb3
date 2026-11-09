import socketserver
import threading
import smtplib
import sys

PORT = 2525

# bacground smtp server (receiver)
# cand cineva se conectează la IP-ul celuilalt client pe portul 2525, serverul raspunde cu codul standard SMTP 220
class SMTPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        peer_ip = self.client_address[0]
        self.request.sendall(b'220 Local SMTP Server Ready\r\n')

        collecting_data = False
        message_buffer = []

        while True:
            #asculta fluxul de date trimis de client. cand detecteaza comanda DATA si sfarsitul mesajului (.\r\n), extrage continutul si il afiseaza in terminal.
            try:
                data = self.request.recv(1024)
                if not data:
                    break
                text = data.decode('utf-8', errors='ignore')

                if text.upper().startswith('QUIT'):
                    self.request.sendall(b'221 Bye\r\n')
                    break
                elif 'DATA' in text.upper() and not collecting_data:
                    collecting_data = True
                    self.request.sendall(b'354 End data with <CRLF>.<CRLF>\r\n')
                    # extrage orice data trimisa imediat dupa comanda DATA
                    parts = text.split('\r\n', 1)
                    if len(parts) > 1 and parts[1]:
                        message_buffer.append(parts[1])
                    continue

                if collecting_data:
                    message_buffer.append(text)
                    full_msg = ''.join(message_buffer)
                    if '\r\n.\r\n' in full_msg or full_msg.endswith('\n.\n') or full_msg.strip().endswith('.'):
                        collecting_data = False
                        clean_msg = full_msg.replace('\r\n.\r\n', '').replace('\n.\n', '').strip()
                        print(f'\n\n[NEW INCOMING MESSAGE from {peer_ip}]')
                        print('='*40)
                        print(clean_msg)
                        print('='*40 + '\n')
                        self.request.sendall(b'250 OK: message queued\r\n')
                        print('Choose an option [1 to Send, 2 to Exit]: ', end='', flush=True)
                else:
                    self.request.sendall(b'250 OK\r\n')
            except Exception:
                break


#porneste serverul pe toate interfetele de retea '0.0.0.0' folosind multi threading. poti trimite si primi mesaje in acelasi timp fara ca aplicatia sa se blocheze
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def start_server():
    server = ThreadedTCPServer(('0.0.0.0', PORT), SMTPHandler)
    server.serve_forever()

# partea  client sender
# foloseste libraria nativa smtplib din python
# se conecteaza la IP-ul colegului pe portul 2525
# trimite un mesaj simplu format din subiect si corpul mesajului
def send_message(partner_ip):
    print(f'\n--- Send Message to Partner ({partner_ip}) ---')
    subject = input('Enter Subject: ')
    body = input('Enter Message Body: ')

    try:
        client = smtplib.SMTP(partner_ip, PORT, timeout=5)
        client.sendmail('adriana@local.net', 'partner@local.net', f'Subject: {subject}\n\n{body}')
        client.quit()
        print('Message sent successfully!\n')
    except Exception as e:
        print(f'Failed to send message: {e}\n')

# loop meniu principal
if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()


    print('TERMINAL SMTP CHAT APP\n')
    partner_ip = input('Enter your partner\'s Tailscale IP (e.g. 100.x.y.z): ').strip()

    while True:
        print('\n--- MENU ---')
        print('1. Send a message to your partner')
        print('2. Exit')
        choice = input('Select an option (1 or 2): ').strip()

        if choice == '1':
            send_message(partner_ip)
        elif choice == '2':
            print('Exiting chat. Goodbye!')
            sys.exit(0)
        else:
            print('Invalid choice. Please enter 1 or 2.')
