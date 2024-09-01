import asyncio
import websockets
import os
import json

# Chemin du dossier à synchroniser
SYNC_FOLDER = "TOSYNC"


async def send_files():
    print("Connexion au serveur pour envoyer des fichiers...")
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connexion établie.")
        await websocket.send("SEND_FILES")

        def get_file_structure(base_path):
            file_structure = {}
            for root, dirs, files in os.walk(base_path):
                rel_root = os.path.relpath(root, base_path)
                if rel_root == ".":
                    rel_root = ""
                file_structure[rel_root] = files
            return file_structure

        file_structure = get_file_structure(SYNC_FOLDER)
        print(f"Structure des fichiers à envoyer : {file_structure}")

        await websocket.send(json.dumps(file_structure))

        for dirpath, filenames in file_structure.items():
            for filename in filenames:
                file_path = os.path.join(SYNC_FOLDER, dirpath, filename)
                print(f"Envoi du fichier : {file_path}")
                with open(file_path, "rb") as file:
                    file_data = file.read()
                    await websocket.send(
                        json.dumps(
                            {
                                "filename": os.path.join(dirpath, filename),
                                "filesize": len(file_data),
                            }
                        )
                    )
                    await websocket.send(file_data)

        await websocket.send("END_OF_FILES")
        print("Envoi terminé.")


async def receive_files():
    print("Connexion au serveur pour recevoir des fichiers...")
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connexion établie.")
        await websocket.send("RECEIVE_FILES")

        file_structure = await websocket.recv()
        print(f"Structure des fichiers reçue : {file_structure}")

        file_structure = json.loads(file_structure)

        # Créer les dossiers nécessaires dans le répertoire TOSYNC
        for folder in file_structure:
            os.makedirs(os.path.join("TOSYNC", folder), exist_ok=True)

        while True:
            try:
                file_info = await websocket.recv()
                if file_info == "END_OF_FILES":
                    print("Fin de la réception des fichiers.")
                    break
                file_info = json.loads(file_info)

                file_data = await websocket.recv()
                print(
                    f"Réception des données pour le fichier : {file_info['filename']}"
                )

                file_path = os.path.join("TOSYNC", file_info["filename"])
                os.makedirs(
                    os.path.dirname(file_path), exist_ok=True
                )  # Assurez-vous que le répertoire existe
                with open(file_path, "wb") as file:
                    file.write(file_data)

                print(f"Fichier reçu et sauvegardé : {file_info['filename']}")
            except websockets.exceptions.ConnectionClosed:
                print("Connexion fermée.")
                break


# Choisissez la fonction à exécuter : send_files ou receive_files
async def main():
    # Choisir entre send_files et receive_files
    # Pour envoyer des fichiers, décommentez la ligne suivante :
    # await send_files()

    # Pour recevoir des fichiers, décommentez la ligne suivante :
    # await receive_files()

    while True:
        input_text = input("Que voulez-vous faire ? (1.send/2.receive/3.exit) : ")
        if input_text == "1":
            await send_files()
        elif input_text == "2":
            await receive_files()
        elif input_text == "3":
            break
        else:
            print("Commande invalide.")


asyncio.run(main())
