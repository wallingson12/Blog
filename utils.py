# utils.py
import os
from werkzeug.utils import secure_filename

def save_upload(file_storage, upload_folder, allowed_extensions=None):
    """
    Salva o arquivo enviado e retorna o nome salvo.
    Se não houver arquivo ou ele não for permitido, retorna None.
    """
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)

    if allowed_extensions:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return None

    path = os.path.join(upload_folder, filename)
    file_storage.save(path)
    return filename


# utils.py
def processar_avatar_upload(arquivo, pasta_destino, genero, extensoes_permitidas):
    """
    Lida com o upload do avatar ou define o avatar padrão baseado no gênero.
    """
    avatar_filename = save_upload(arquivo, pasta_destino, allowed_extensions=extensoes_permitidas)
    if not avatar_filename:
        avatar_filename = get_default_avatar(genero)
    return avatar_filename

def get_default_avatar(gender):
    """Retorna o avatar padrão baseado no gênero"""
    return 'default_men_avatar.jpg' if gender == 'Masculino' else 'default_women_avatar.jpg'

def processar_imagem_post(arquivo, pasta_destino, extensoes_permitidas):
    return save_upload(arquivo, pasta_destino, allowed_extensions=extensoes_permitidas)
