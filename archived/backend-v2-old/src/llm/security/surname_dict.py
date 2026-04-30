"""
中文姓氏词典模块
用于精确识别和处理中文姓名的脱敏
"""

import re
from typing import List, Tuple


class SurnameDict:
    """中文姓氏词典，用于识别文本中的中文姓名"""
    
    def __init__(self):
        # 常见的中文姓氏列表（百家姓前100个）
        self.surnames = {
            # 单字姓氏
            '王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
            '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
            '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
            '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
            '苏', '卢', '蒋', '蔡', '贾', '丁', '魏', '薛', '叶', '阎',
            '余', '潘', '杜', '戴', '夏', '钟', '汪', '田', '任', '姜',
            '范', '方', '石', '姚', '谭', '廖', '邹', '熊', '金', '陆',
            '郝', '孔', '白', '崔', '康', '毛', '邱', '秦', '江', '史',
            '顾', '侯', '邵', '孟', '龙', '万', '段', '漕', '钱', '汤',
            '尹', '黎', '易', '常', '武', '乔', '贺', '赖', '龚', '文',
            
            # 复姓
            '欧阳', '太史', '端木', '上官', '司马', '东方', '独孤', '南宫', '万俟', '闻人',
            '夏侯', '诸葛', '尉迟', '公羊', '赫连', '澹台', '皇甫', '宗政', '濮阳', '公冶',
            '太叔', '申屠', '公孙', '慕容', '仲孙', '钟离', '长孙', '宇文', '司徒', '鲜于'
        }
        
        # 按长度排序，优先匹配长姓氏（复姓）
        self.sorted_surnames = sorted(self.surnames, key=len, reverse=True)
    
    def find_names_in_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        在文本中查找可能的中文姓名
        返回: [(姓名, 开始位置, 结束位置), ...]
        """
        names_found = []
        
        # 使用正则表达式匹配可能的姓名模式
        # 姓氏 + 1-3个中文字符
        for surname in self.sorted_surnames:
            # 构建匹配模式：姓氏后跟1-3个中文字符，且不在其他中文字符中间
            pattern = f'(?<![\\u4e00-\\u9fff]){re.escape(surname)}[\\u4e00-\\u9fff]{{1,3}}(?![\\u4e00-\\u9fff])'
            
            for match in re.finditer(pattern, text):
                name = match.group(0)
                start = match.start()
                end = match.end()
                
                # 验证是否是合理的姓名（长度2-4字符）
                if 2 <= len(name) <= 4:
                    # 检查是否与已找到的姓名重叠
                    overlapping = any(
                        start < existing_end and end > existing_start 
                        for _, existing_start, existing_end in names_found
                    )
                    
                    if not overlapping:
                        names_found.append((name, start, end))
        
        # 按位置排序
        names_found.sort(key=lambda x: x[1])
        return names_found
    
    def is_chinese_name(self, text: str) -> bool:
        """判断给定文本是否可能是中文姓名"""
        if not text or len(text) < 2 or len(text) > 4:
            return False
            
        # 检查是否全部是中文字符
        if not re.match(r'^[\u4e00-\u9fff]+$', text):
            return False
            
        # 检查第一个字符是否是已知姓氏
        for surname in self.sorted_surnames:
            if text.startswith(surname):
                return True
                
        return False
    
    def get_surname(self, name: str) -> str:
        """从姓名中提取姓氏"""
        for surname in self.sorted_surnames:
            if name.startswith(surname):
                return surname
        
        # 如果没有匹配到已知姓氏，返回第一个字符
        return name[0] if name else ""