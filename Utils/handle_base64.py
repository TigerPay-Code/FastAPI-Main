import hashlib
import os


class MD5Utils:
    """
    MD5加密工具类，提供字符串加密和文件MD5计算功能
    返回格式: (status, result_or_error)
    status: 操作状态 (SUCCESS, ERROR)
    result_or_error: 成功时返回结果，失败时返回错误信息字典
    """

    # 错误码定义
    ERROR_CODES = {
        "INVALID_INPUT_TYPE": 2001,
        "EMPTY_INPUT": 2002,
        "FILE_NOT_FOUND": 2003,
        "FILE_READ_ERROR": 2004,
        "UNKNOWN_ERROR": 2099
    }

    @staticmethod
    def md5_string(data: str) -> tuple:
        """
        计算字符串的MD5值
        :param data: 要加密的字符串
        :return: (status, result) 元组
        """
        try:
            # 输入验证
            if not isinstance(data, str):
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["INVALID_INPUT_TYPE"],
                    "message": "输入必须是字符串类型",
                    "input": data
                })

            if not data:
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["EMPTY_INPUT"],
                    "message": "输入不能为空字符串",
                    "input": data
                })

            # 计算MD5
            md5_hash = hashlib.md5()
            md5_hash.update(data.encode('utf-8'))
            return ("SUCCESS", md5_hash.hexdigest())

        except Exception as e:
            return ("ERROR", {
                "code": MD5Utils.ERROR_CODES["UNKNOWN_ERROR"],
                "message": f"MD5计算失败: {str(e)}",
                "input": data,
                "exception": str(e)
            })

    @staticmethod
    def md5_file(file_path: str, chunk_size: int = 8192) -> tuple:
        """
        计算文件的MD5值
        :param file_path: 文件路径
        :param chunk_size: 读取块大小(字节)
        :return: (status, result) 元组
        """
        try:
            # 输入验证
            if not isinstance(file_path, str):
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["INVALID_INPUT_TYPE"],
                    "message": "文件路径必须是字符串类型",
                    "input": file_path
                })

            if not file_path:
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["EMPTY_INPUT"],
                    "message": "文件路径不能为空",
                    "input": file_path
                })

            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["FILE_NOT_FOUND"],
                    "message": f"文件不存在: {file_path}",
                    "input": file_path
                })

            # 检查是否为文件
            if not os.path.isfile(file_path):
                return ("ERROR", {
                    "code": MD5Utils.ERROR_CODES["FILE_NOT_FOUND"],
                    "message": f"路径不是文件: {file_path}",
                    "input": file_path
                })

            # 计算文件MD5
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
            return ("SUCCESS", md5_hash.hexdigest())

        except PermissionError as e:
            return ("ERROR", {
                "code": MD5Utils.ERROR_CODES["FILE_READ_ERROR"],
                "message": f"文件读取权限不足: {str(e)}",
                "input": file_path,
                "exception": str(e)
            })
        except OSError as e:
            return ("ERROR", {
                "code": MD5Utils.ERROR_CODES["FILE_READ_ERROR"],
                "message": f"文件读取错误: {str(e)}",
                "input": file_path,
                "exception": str(e)
            })
        except Exception as e:
            return ("ERROR", {
                "code": MD5Utils.ERROR_CODES["UNKNOWN_ERROR"],
                "message": f"文件MD5计算失败: {str(e)}",
                "input": file_path,
                "exception": str(e)
            })


# 测试用例
if __name__ == '__main__':
    # 测试字符串MD5
    test_strings = [
        "Hello World",
        "密码123",
        "",  # 空字符串
        123,  # 非字符串类型
    ]

    print("字符串MD5测试:")
    for data in test_strings:
        status, result = MD5Utils.md5_string(data)
        if status == "SUCCESS":
            print(f"✅ '{data}' -> {result}")
        else:
            print(f"❌ '{data}': {result['message']} [错误码 {result['code']}]")

    # 测试文件MD5
    import tempfile

    print("\n文件MD5测试:")

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"File content for MD5 test")
        tmp_path = tmp_file.name

    # 有效文件测试
    status, result = MD5Utils.md5_file(tmp_path)
    if status == "SUCCESS":
        print(f"✅ 临时文件MD5: {result}")
    else:
        print(f"❌ 临时文件MD5失败: {result['message']}")

    # 无效文件测试
    test_files = [
        "non_existent_file.txt",  # 不存在的文件
        os.path.dirname(tmp_path),  # 目录路径
        "",  # 空路径
        123,  # 非字符串类型
    ]

    for file_path in test_files:
        status, result = MD5Utils.md5_file(file_path)
        if status == "SUCCESS":
            print(f"✅ '{file_path}' -> {result}")
        else:
            print(f"❌ '{file_path}': {result['message']} [错误码 {result['code']}]")

    # 清理临时文件
    os.unlink(tmp_path)
import base64
import binascii


class Base64Utils:
    """
    Base64编码解码工具类，提供状态返回和错误码机制
    返回格式: (status, result_or_error)
    status: 操作状态 (SUCCESS, ERROR)
    result_or_error: 成功时返回结果，失败时返回错误信息字典
    """

    # 错误码定义
    ERROR_CODES = {
        "INVALID_INPUT_TYPE": 1001,
        "EMPTY_INPUT": 1002,
        "INVALID_BASE64": 1003,
        "DECODING_ERROR": 1004,
        "UNKNOWN_ERROR": 1099
    }

    @staticmethod
    def encode(data: str) -> tuple:
        """
        Base64编码
        返回: (status, result)
        status: "SUCCESS" 或 "ERROR"
        result: 成功时为编码字符串，失败时为错误信息字典
        """
        try:
            # 输入验证
            if not isinstance(data, str):
                return ("ERROR", {
                    "code": Base64Utils.ERROR_CODES["INVALID_INPUT_TYPE"],
                    "message": "输入必须是字符串类型",
                    "input": data
                })

            if not data:
                return ("ERROR", {
                    "code": Base64Utils.ERROR_CODES["EMPTY_INPUT"],
                    "message": "输入不能为空字符串",
                    "input": data
                })

            # 执行编码
            byte_data = data.encode('utf-8')
            encoded_bytes = base64.b64encode(byte_data)
            return ("SUCCESS", encoded_bytes.decode('utf-8'))

        except Exception as e:
            return ("ERROR", {
                "code": Base64Utils.ERROR_CODES["UNKNOWN_ERROR"],
                "message": f"编码过程中发生未知错误: {str(e)}",
                "input": data,
                "exception": str(e)
            })

    @staticmethod
    def decode(encoded_data: str) -> tuple:
        """
        Base64解码
        返回: (status, result)
        status: "SUCCESS" 或 "ERROR"
        result: 成功时为解码字符串，失败时为错误信息字典
        """
        try:
            # 输入验证
            if not isinstance(encoded_data, str):
                return ("ERROR", {
                    "code": Base64Utils.ERROR_CODES["INVALID_INPUT_TYPE"],
                    "message": "输入必须是字符串类型",
                    "input": encoded_data
                })

            if not encoded_data:
                return ("ERROR", {
                    "code": Base64Utils.ERROR_CODES["EMPTY_INPUT"],
                    "message": "输入不能为空字符串",
                    "input": encoded_data
                })

            # 执行解码
            byte_data = encoded_data.encode('utf-8')
            decoded_bytes = base64.b64decode(byte_data, validate=True)
            return ("SUCCESS", decoded_bytes.decode('utf-8'))

        except binascii.Error as e:
            return ("ERROR", {
                "code": Base64Utils.ERROR_CODES["INVALID_BASE64"],
                "message": f"无效的Base64格式: {str(e)}",
                "input": encoded_data,
                "exception": str(e)
            })

        except UnicodeDecodeError as e:
            return ("ERROR", {
                "code": Base64Utils.ERROR_CODES["DECODING_ERROR"],
                "message": "解码后的字节不是有效的UTF-8格式",
                "input": encoded_data,
                "exception": str(e)
            })

        except Exception as e:
            return ("ERROR", {
                "code": Base64Utils.ERROR_CODES["UNKNOWN_ERROR"],
                "message": f"解码过程中发生未知错误: {str(e)}",
                "input": encoded_data,
                "exception": str(e)
            })


# 程序调用示例
if __name__ == '__main__':
    # 示例1: 正常编码解码
    status, result = Base64Utils.encode("Hello World!")
    if status == "SUCCESS":
        print(f"编码成功: {result}")
        # 解码验证
        d_status, d_result = Base64Utils.decode(result)
        if d_status == "SUCCESS":
            print(f"解码成功: {d_result}")
        else:
            print(f"解码失败: {d_result['message']}")
    else:
        print(f"编码失败: {result['message']}")

    # 示例2: 处理错误输入
    test_cases = [
        "",  # 空字符串
        123,  # 非字符串类型
        "Invalid!@",  # 无效Base64格式
    ]

    for data in test_cases:
        print(f"\n测试输入: {repr(data)}")
        if isinstance(data, str):
            # 解码测试
            status, result = Base64Utils.decode(data)
            if status == "SUCCESS":
                print(f"✅ 解码成功: {result}")
            else:
                print(f"❌ 解码失败 [错误码 {result['code']}]: {result['message']}")
        else:
            # 编码测试
            status, result = Base64Utils.encode(data)
            if status == "SUCCESS":
                print(f"✅ 编码成功: {result}")
            else:
                print(f"❌ 编码失败 [错误码 {result['code']}]: {result['message']}")

import bcrypt
import re
from getpass import getpass


class PasswordUtils:
    """
    密码哈希加密与验证工具类
    使用bcrypt算法进行安全的密码哈希处理
    """

    # 错误码定义
    ERROR_CODES = {
        "INVALID_PASSWORD_FORMAT": 3001,
        "HASHING_ERROR": 3002,
        "VERIFICATION_ERROR": 3003
    }

    @staticmethod
    def hash_password(password: str) -> tuple:
        """
        密码哈希加密函数
        :param password: 原始密码字符串
        :return: (status, result)
                成功: ("SUCCESS", 哈希后的密码字符串)
                失败: ("ERROR", 错误信息字典)
        """
        try:
            # 验证密码格式
            if not PasswordUtils._is_valid_password(password):
                return ("ERROR", {
                    "code": PasswordUtils.ERROR_CODES["INVALID_PASSWORD_FORMAT"],
                    "message": "密码必须包含大小写字母、数字和特殊字符，长度8-64位"
                })

            # 生成盐值并哈希密码
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return ("SUCCESS", hashed.decode('utf-8'))

        except Exception as e:
            return ("ERROR", {
                "code": PasswordUtils.ERROR_CODES["HASHING_ERROR"],
                "message": f"密码哈希失败: {str(e)}",
                "exception": str(e)
            })

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> tuple:
        """
        密码验证函数
        :param password: 待验证的原始密码
        :param hashed_password: 存储的哈希密码
        :return: (status, result)
                成功: ("SUCCESS", 验证结果布尔值)
                失败: ("ERROR", 错误信息字典)
        """
        try:
            # 验证密码格式
            if not PasswordUtils._is_valid_password(password):
                return ("ERROR", {
                    "code": PasswordUtils.ERROR_CODES["INVALID_PASSWORD_FORMAT"],
                    "message": "密码必须包含大小写字母、数字和特殊字符，长度8-64位"
                })

            # 验证密码是否匹配
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
            return ("SUCCESS", is_valid)

        except Exception as e:
            return ("ERROR", {
                "code": PasswordUtils.ERROR_CODES["VERIFICATION_ERROR"],
                "message": f"密码验证失败: {str(e)}",
                "exception": str(e)
            })

    @staticmethod
    def _is_valid_password(password: str) -> bool:
        """
        验证密码复杂度
        :param password: 密码字符串
        :return: 是否符合复杂度要求
        """
        if len(password) < 8 or len(password) > 64:
            return False

        # 检查是否包含大小写字母、数字和特殊字符
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)

        return has_upper and has_lower and has_digit and has_special


# 测试用例
if __name__ == '__main__':
    print("密码哈希与验证测试")
    print("=" * 40)

    # 测试用例数据
    test_passwords = [
        "ValidPass1!",  # 有效密码
        "weak",  # 太短
        "no_upper1!",  # 缺少大写
        "NO_LOWER1!",  # 缺少小写
        "NoDigit!",  # 缺少数字
        "NoSpecial123",  # 缺少特殊字符
        "A" * 65,  # 太长
    ]

    # 测试哈希和验证
    for pwd in test_passwords:
        print(f"\n测试密码: {pwd}")

        # 哈希测试
        status, result = PasswordUtils.hash_password(pwd)
        if status == "SUCCESS":
            print(f"哈希成功: {result}")

            # 验证测试
            verify_status, verify_result = PasswordUtils.verify_password(pwd, result)
            if verify_status == "SUCCESS":
                print(f"验证结果: {'成功' if verify_result else '失败'}")
            else:
                print(f"验证错误: {verify_result['message']}")
        else:
            print(f"哈希错误: {result['message']}")

    # 模拟用户注册和登录流程
    print("\n模拟用户注册和登录流程")
    print("-" * 40)

    # 注册流程
    while True:
        reg_password = getpass("请设置密码(8-64位，包含大小写字母、数字和特殊字符): ")
        status, hashed = PasswordUtils.hash_password(reg_password)

        if status == "SUCCESS":
            print("密码设置成功!")
            stored_hash = hashed
            break
        else:
            print(f"密码不符合要求: {hashed['message']}")

    # 登录流程
    while True:
        login_password = getpass("请输入密码进行登录: ")
        status, result = PasswordUtils.verify_password(login_password, stored_hash)

        if status == "SUCCESS":
            if result:
                print("登录成功!")
                break
            else:
                print("密码错误，请重试")
        else:
            print(f"验证错误: {result['message']}")
