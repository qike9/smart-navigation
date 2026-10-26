# data/data_encryption.py
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import json
from typing import Any, Dict


class DataEncryptor:
    """数据加密器，使用AES算法"""

    def __init__(self, key: str = None):
        """初始化加密器

        Args:
            key: 加密密钥，必须是16、24或32字节
        """
        self.key = key.encode('utf-8') if key else b'1234567890123456'

    def encrypt(self, data: Any) -> str:
        """加密数据

        Args:
            data: 要加密的数据

        Returns:
            str: base64编码的加密字符串
        """
        # 将数据转换为JSON字符串
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            data_str = str(data)

        # 生成随机IV
        iv = get_random_bytes(AES.block_size)

        # 创建加密器
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # 加密数据
        encrypted_bytes = cipher.encrypt(pad(data_str.encode('utf-8'), AES.block_size))

        # 合并IV和加密数据
        combined = iv + encrypted_bytes

        # 返回base64编码
        return base64.b64encode(combined).decode('utf-8')

    def decrypt(self, encrypted_data: str) -> Any:
        """解密数据

        Args:
            encrypted_data: base64编码的加密字符串

        Returns:
            Any: 解密后的数据
        """
        # 解码base64
        combined = base64.b64decode(encrypted_data)

        # 提取IV和加密数据
        iv = combined[:AES.block_size]
        encrypted_bytes = combined[AES.block_size:]

        # 创建解密器
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # 解密数据
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)

        # 转换为字符串
        data_str = decrypted_bytes.decode('utf-8')

        # 尝试解析为JSON
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return data_str

    def encrypt_user_data(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """加密用户数据

        Args:
            user_data: 用户数据字典

        Returns:
            Dict[str, str]: 加密后的数据
        """
        encrypted = {}
        for key, value in user_data.items():
            if key != 'user_id':  # 不加密ID
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_user_data(self, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """解密用户数据

        Args:
            encrypted_data: 加密的用户数据

        Returns:
            Dict[str, Any]: 解密后的数据
        """
        decrypted = {}
        for key, value in encrypted_data.items():
            if key != 'user_id':  # 不解密ID
                decrypted[key] = self.decrypt(value)
            else:
                decrypted[key] = value
        return decrypted


# 测试加密功能
if __name__ == "__main__":
    encryptor = DataEncryptor("1234567890123456")

    # 测试加密解密
    test_data = {"name": "张三", "age": 25, "preferences": {"voice": True}}
    encrypted = encryptor.encrypt(test_data)
    print(f"加密后: {encrypted}")

    decrypted = encryptor.decrypt(encrypted)
    print(f"解密后: {decrypted}")