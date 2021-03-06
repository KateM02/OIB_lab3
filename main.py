import json
import argparse  # работа с командной строкой
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


settings = {
	'initial_file': 'file.txt',  # путь к исходному файлу
	'encrypted_file': 'encrypted_file.txt',  # путь к зашифрованному файлу
	'decrypted_file': 'decrypted_file.txt',  # путь к расшифрованному файлу
	'symmetric_key': 'symmetric_key.txt',  # путь к симметричному ключу
	'public_key': 'public_key.pem',  # путь к открытому ключу
	'secret_key': 'secret_key.pem',  # путь к закрытому ключу
	'vec_init': 'iv.txt'
}


parser = argparse.ArgumentParser()
parser.add_argument('mode', help='Режим работы')
args = parser.parse_args()


def generation(symmetric_k, public_k, secret_k):
	# сериализация ключа симмеричного алгоритма в файл
	print("Длина ключа от 5 до 16 байт")
	key_len = int(input('Введите желаемую длину ключа: '))
	while key_len < 5 or key_len > 16:
		key_len = int(input('Введите желаемую длину ключа: '))
	key = os.urandom(key_len)
	# генерация пары ключей для асимметричного алгоритма шифрования
	keys = rsa.generate_private_key(
		public_exponent=65537,
		key_size=2048
	)
	private_key = keys
	public_key = keys.public_key()
	from cryptography.hazmat.primitives.asymmetric import padding
	c_key = public_key.encrypt(key,
							   padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
								algorithm=hashes.SHA256(), label=None))
	with open(symmetric_k, 'wb') as key_file:
		key_file.write(c_key)
	# сериализация открытого ключа в файл
	with open(public_k, 'wb') as public_out:
		public_out.write(public_key.public_bytes(encoding=serialization.Encoding.PEM,
												 format=serialization.PublicFormat.SubjectPublicKeyInfo))
	# сериализация закрытого ключа в файл
	with open(secret_k, 'wb') as private_out:
		private_out.write(private_key.private_bytes(encoding=serialization.Encoding.PEM,
													format=serialization.PrivateFormat.TraditionalOpenSSL,
													encryption_algorithm=serialization.NoEncryption()))

	print(f'Ключи асимметричного шифрования сериализованы по адресу: {public_k}\t{secret_k}')
	print(f"Ключ симметричного шифрования:\t{symmetric_k}\n")
	pass


def encryption(inital_f, secret_k, symmetric_k, encrypted_f, vec_init):
	with open(secret_k, 'rb') as pem_in:
		private_bytes = pem_in.read()
	private_key = load_pem_private_key(private_bytes, password=None, )
	with open(symmetric_k, 'rb') as key:
		symmetric_bytes = key.read()
	from cryptography.hazmat.primitives.asymmetric import padding
	d_key = private_key.decrypt(symmetric_bytes,
								padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(),
											 label=None))

	print(f"Ключ: {d_key}")
	with open(inital_f, 'rb') as o_text:
		text = o_text.read()
	from cryptography.hazmat.primitives import padding
	pad = padding.ANSIX923(64).padder()
	padded_text = pad.update(text) + pad.finalize()
	# случайное значение для инициализации блочного режима, должно быть размером с блок и каждый раз новым
	iv = os.urandom(8)
	with open(vec_init, 'wb') as iv_file:
		iv_file.write(iv)
	cipher = Cipher(algorithms.CAST5(d_key), modes.CBC(iv))
	encryptor = cipher.encryptor()
	c_text = encryptor.update(padded_text) + encryptor.finalize()
	with open(encrypted_f, 'wb') as encrypt_file:
		encrypt_file.write(c_text)
	print(f"Текст зашифрован и сериализован по адресу: {encrypted_f}\n")
	pass


def decryption(encrypted_f, secret_k, symmetric_k, decrypted_file, vec_init):
	with open(secret_k, 'rb') as pem_in:
		private_bytes = pem_in.read()
	private_key = load_pem_private_key(private_bytes, password=None, )
	with open(symmetric_k, 'rb') as key:
		symmetric_bytes = key.read()
	from cryptography.hazmat.primitives.asymmetric import padding
	d_key = private_key.decrypt(symmetric_bytes,
								padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(),
											 label=None))
	with open(encrypted_f, 'rb') as e_text:
		text = e_text.read()
	# дешифрование и депаддинг текста симметричным алгоритмом
	with open(vec_init, 'rb') as iv_file:
		iv = iv_file.read()
	cipher = Cipher(algorithms.CAST5(d_key), modes.CBC(iv))
	decrypter = cipher.decryptor()
	from cryptography.hazmat.primitives import padding
	unpadded = padding.ANSIX923(64).unpadder()
	d_text = unpadded.update(decrypter.update(text) + decrypter.finalize()) + unpadded.finalize()
	# print("Расшифрованный текст:")
	# print(d_text.decode('UTF-8'))
	with open(decrypted_file, 'w', encoding='UTF-8') as decrypt_file:
		decrypt_file.write(d_text.decode('UTF-8'))
	print(f"Текст расшифрован и сериализован по адресу:  {decrypted_file}\n")
	pass


while True:
	if args.mode == 'gen':
		print('Генерация ключей гибридной системы')
		if not os.path.exists('settings.json'):
			with open('settings.json', 'w') as fp:
				json.dump(settings, fp)
		with open('settings.json', 'r') as json_file:
			settings_data = json.load(json_file)
		generation(settings_data['symmetric_key'], settings_data['public_key'], settings_data['secret_key'])
		break
	elif args.mode == 'enc':
		print('Шифрование данных гибридной системой')
		if not os.path.exists('settings.json'):
			with open('settings.json', 'w') as fp:
				json.dump(settings, fp)
		with open('settings.json', 'r') as json_file:
			settings_data = json.load(json_file)
		if not os.path.exists('file.txt'):
			print('Не найден файл с исходным текстом.')
			break
		if not os.path.exists(settings_data['secret_key']):
			print('Не найден закрытый ключ. Используйте сначала режим gen')
			break
		if not os.path.exists(settings_data['symmetric_key']):
			print('Не найден симметричный ключ. Используйте сначала режим gen')
			break
		encryption(settings_data['initial_file'], settings_data['secret_key'],
				   settings_data['symmetric_key'], settings_data['encrypted_file'], settings_data['vec_init'])
		break
	elif args.mode == 'dec':
		print('Дешифрование данных гибридной системой')
		if not os.path.exists('settings.json'):
			with open('settings.json', 'w') as fp:
				json.dump(settings, fp)
		with open('settings.json', 'r') as json_file:
			settings_data = json.load(json_file)
		if not os.path.exists(settings_data['secret_key']):
			print('Не найден закрытый ключ. Используйте сначала режим gen')
			break
		if not os.path.exists(settings_data['symmetric_key']):
			print('Не найден симметричный ключ. Используйте сначала режим gen')
			break
		if not os.path.exists(settings_data['encrypted_file']):
			print('Не найден зашифрованный файл. Используйте сначала режим enc')
			break
		decryption(settings_data['encrypted_file'], settings_data['secret_key'],
				   settings_data['symmetric_key'], settings_data['decrypted_file'], settings_data['vec_init'])
		break
	elif args.mode == 'all':
		print('Запущен режим общего теста')
		if not os.path.exists('settings.json'):
			with open('settings.json', 'w') as fp:
				json.dump(settings, fp)
		with open('settings.json', 'r') as json_file:
			settings_data = json.load(json_file)
		generation(settings_data['symmetric_key'], settings_data['public_key'], settings_data['secret_key'])
		if not os.path.exists('file.txt'):
			print('Не найден файл с исходным текстом.')
			break
		encryption(settings_data['initial_file'], settings_data['secret_key'],
				   settings_data['symmetric_key'], settings_data['encrypted_file'], settings_data['vec_init'])
		decryption(settings_data['encrypted_file'], settings_data['secret_key'],
				   settings_data['symmetric_key'], settings_data['decrypted_file'], settings_data['vec_init'])
		break
	else:
		print('Нет такого режима работы')
		break
