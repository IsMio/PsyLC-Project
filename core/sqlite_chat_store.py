import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional


class SQLiteChatStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库，检查必要的表是否存在"""
        with sqlite3.connect(self.db_path) as conn:
            print("connecting to database..."+self.db_path)
            cursor = conn.cursor()
            cursor = conn.cursor()
            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            
            # 检查users表是否存在
            cursor.execute("PRAGMA table_info(users);")
            if not cursor.fetchall():
                raise Exception("数据库表不存在: users")
            
            # 检查chat_sessions表是否存在
            cursor.execute("PRAGMA table_info(chat_sessions);")
            if not cursor.fetchall():
                raise Exception("数据库表不存在: chat_sessions")
            
            # 检查chat_messages表是否存在
            cursor.execute("PRAGMA table_info(chat_messages);")
            if not cursor.fetchall():
                raise Exception("数据库表不存在: chat_messages")
            
            # 检查message_attachments表是否存在
            cursor.execute("PRAGMA table_info(message_attachments);")
            if not cursor.fetchall():
                raise Exception("数据库表不存在: message_attachments")
            
            print("connected to database and verified tables")

    def _get_user(self, user_id: str) -> Optional[str]:
        """获取用户ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 查找用户
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                return user[0]
            return None

    def _get_session_id(self, user_id: str, chat_name: str) -> Optional[str]:
        """根据用户ID和聊天名称获取会话ID"""
        print(f"_get_session_id: user_id={user_id}, chat_name={chat_name}")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 先尝试根据id查询（因为chat_name实际上是session_id）
            cursor.execute(
                "SELECT id FROM chat_sessions WHERE user_id = ? AND id = ? AND deleted_at IS NULL",
                (user_id, chat_name)
            )
            session = cursor.fetchone()
            print(f"_get_session_id: id query result={session}")
            if session:
                return session[0]
            
            # 再尝试根据title查询（兼容旧数据）
            cursor.execute(
                "SELECT id FROM chat_sessions WHERE user_id = ? AND title = ? AND deleted_at IS NULL",
                (user_id, chat_name)
            )
            session = cursor.fetchone()
            print(f"_get_session_id: title query result={session}")
            return session[0] if session else None

    def list_chat_names(self, user_id: str) -> List[str]:
        """获取用户的聊天列表"""
        if not self._get_user(user_id):
            return []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM chat_sessions WHERE user_id = ? AND deleted_at IS NULL ORDER BY created_at",
                (user_id,)
            )
            chats = [row[0] for row in cursor.fetchall()]
            return chats

    def count_chats(self, user_id: str) -> int:
        """获取用户的聊天数量"""
        if not self._get_user(user_id):
            return 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM chat_sessions WHERE user_id = ? AND deleted_at IS NULL",
                (user_id,)
            )
            return cursor.fetchone()[0]

    def load_chat(self, user_id: str, chat_name: str) -> Optional[Dict[str, Any]]:
        """加载聊天内容"""
        if not self._get_user(user_id):
            return None
        session_id = self._get_session_id(user_id, chat_name)
        print(f"load_chat: user_id={user_id}, chat_name={chat_name}, session_id={session_id}")
        if not session_id:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 获取消息，包括token_count和model
            cursor.execute(
                "SELECT id, role, content, parent_id, token_count, model, created_at FROM chat_messages WHERE session_id = ? ORDER BY seq",
                (session_id,)
            )
            messages = []
            for message_id, role, content, parent_id, token_count, model, created_at in cursor.fetchall():
                messages.append({
                    "id": message_id,
                    "role": role, 
                    "content": content,
                    "parent_id": parent_id,
                    "token_count": token_count,
                    "model": model,
                    "created_at": created_at
                })
            
            # 获取元数据
            cursor.execute(
                "SELECT meta_json FROM chat_sessions WHERE id = ?",
                (session_id,)
            )
            meta_json = cursor.fetchone()[0]
            meta_data = json.loads(meta_json) if meta_json else {}
            
            # 构建返回数据
            data = {
                "messages": messages,
                "total_times": meta_data.get("total_times", []),
                "model_names": meta_data.get("model_names", []),
                "turn_costs": meta_data.get("turn_costs", []),
                "current_times": meta_data.get("current_times", [])
            }
            
            return data

    def save_chat(self, user_id: str, chat_name: str, data: Dict[str, Any]) -> None:
        """保存聊天内容"""
        if not self._get_user(user_id):
            return
        session_id = self._get_session_id(user_id, chat_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建或更新会话
            if not session_id:
                # 使用chat_name作为会话ID，确保与API接口返回的session_id一致
                session_id = chat_name
                meta_json = json.dumps({
                    "total_times": data.get("total_times", []),
                    "model_names": data.get("model_names", []),
                    "turn_costs": data.get("turn_costs", []),
                    "current_times": data.get("current_times", [])
                })
                
                try:
                    # 尝试创建新会话
                    cursor.execute(
                        "INSERT INTO chat_sessions (id, user_id, title, meta_json) VALUES (?, ?, ?, ?)",
                        (session_id, user_id, chat_name, meta_json)
                    )
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed: chat_sessions.id" in str(e):
                        # 如果会话ID已经存在，尝试更新它
                        cursor.execute(
                            "UPDATE chat_sessions SET user_id = ?, title = ?, deleted_at = NULL, updated_at = strftime('%s', 'now'), meta_json = ? WHERE id = ?",
                            (user_id, chat_name, meta_json, session_id)
                        )
                    else:
                        raise
            else:
                meta_json = json.dumps({
                    "total_times": data.get("total_times", []),
                    "model_names": data.get("model_names", []),
                    "turn_costs": data.get("turn_costs", []),
                    "current_times": data.get("current_times", [])
                })
                cursor.execute(
                    "UPDATE chat_sessions SET title = ?, updated_at = strftime('%s', 'now'), meta_json = ? WHERE id = ?",
                    (chat_name, meta_json, session_id)
                )
            
            # 只有当messages不为空时才处理消息
            messages = data.get("messages", [])
            if messages:
                # 3. 检查同session的上条message的id，用于parent_id
                parent_id = None
                cursor.execute(
                    "SELECT id FROM chat_messages WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                    (session_id,)
                )
                last_message = cursor.fetchone()
                if last_message:
                    parent_id = last_message[0]
                
                # 获取当前消息数量
                cursor.execute(
                    "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?",
                    (session_id,)
                )
                current_count = cursor.fetchone()[0]
                
                # 无论是否是新会话，都先删除旧消息，然后插入完整的对话历史
                # 这样可以确保所有消息（包括用户发送的消息）都被正确保存
                cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                
                # 重置parent_id
                parent_id = None
                
                # 插入所有消息
                for seq, msg in enumerate(messages):
                    message_id = str(uuid.uuid4())
                    # 2. 完善保存对话时间消耗的token数以及当前模型
                    token_count = msg.get("token_count", 0)
                    model = msg.get("model", "")
                    
                    cursor.execute(
                        "INSERT INTO chat_messages (id, session_id, role, content, seq, parent_id, token_count, model) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (message_id, session_id, msg.get("role"), msg.get("content"), seq, parent_id, token_count, model)
                    )
                    
                    # 更新parent_id为当前消息ID，用于下一条消息
                    parent_id = message_id
            
            conn.commit()

    def delete_chat(self, user_id: str, chat_name: str) -> None:
        """删除聊天"""
        if not self._get_user(user_id):
            return
        session_id = self._get_session_id(user_id, chat_name)
        if not session_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_sessions SET deleted_at = strftime('%s', 'now') WHERE id = ?",
                (session_id,)
            )
            conn.commit()

    def rename_chat(self, user_id: str, old_chat_name: str, new_chat_name: str) -> None:
        """重命名聊天"""
        if not self._get_user(user_id):
            return
        session_id = self._get_session_id(user_id, old_chat_name)
        if not session_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = strftime('%s', 'now') WHERE id = ?",
                (new_chat_name, session_id)
            )
            conn.commit()

    def get_all_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        if not self._get_user(user_id):
            return []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? AND deleted_at IS NULL ORDER BY updated_at DESC",
                (user_id,)
            )
            sessions = []
            for row in cursor.fetchall():
                session_id, title, created_at, updated_at = row
                sessions.append({
                    "id": session_id,
                    "title": title,
                    "created_at": created_at,
                    "updated_at": updated_at
                })
            return sessions

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取指定会话的历史消息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, role, content, parent_id, token_count, model, created_at FROM chat_messages WHERE session_id = ? ORDER BY seq",
                (session_id,)
            )
            messages = []
            for message_id, role, content, parent_id, token_count, model, created_at in cursor.fetchall():
                messages.append({
                    "id": message_id,
                    "role": role,
                    "content": content,
                    "parent_id": parent_id,
                    "token_count": token_count,
                    "model": model,
                    "created_at": created_at
                })
            return messages
    
    def add_message(self, user_id: str, session_id: str, user_message: Dict[str, Any], assistant_message: Dict[str, Any]) -> None:
        """添加新的消息到会话历史"""
        if not self._get_user(user_id):
            return
        existing_data = self.load_chat(user_id, session_id)
        
        print(f"add_message: user_id={user_id}, session_id={session_id}")
        print(f"add_message: existing_data={existing_data}")
        
        if existing_data and existing_data.get("messages"):
            # 找到最晚的一条记录作为parent
            last_message = existing_data["messages"][-1]
            user_message["parent_id"] = last_message.get("id")
            # 构建新的消息列表，只添加新消息
            new_messages = existing_data["messages"].copy()
            new_messages.append(user_message)
            new_messages.append(assistant_message)
            print(f"add_message: existing messages count={len(existing_data['messages'])}, new messages count={len(new_messages)}")
        else:
            # 新会话，直接添加消息
            new_messages = [user_message, assistant_message]
            print(f"add_message: new session, messages count={len(new_messages)}")
        
        # 构建新的历史记录数据
        new_history = {
            "messages": new_messages,
            "total_times": existing_data.get("total_times", []) if existing_data else [],
            "model_names": existing_data.get("model_names", []) if existing_data else [],
            "turn_costs": existing_data.get("turn_costs", []) if existing_data else [],
            "current_times": existing_data.get("current_times", []) if existing_data else []
        }
        
        # 保存到数据库
        self.save_chat(user_id, session_id, new_history)
