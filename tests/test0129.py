import sqlite3
import json
from tkinter import Tk, Label, Entry, Button, ttk, messagebox, StringVar


# 登录凭据（可修改）
USERNAME = "admin"
PASSWORD = "1234"

# 数据库所有权配置
DB_OWNER = "Admin"


class InfoStorageSystem:
    def __init__(self, db_name="info_system.db"):
        self.conn = None
        self.cursor = None
        self.db_name = db_name
        self.authenticated = False  # 记录登录状态

    def authenticate(self, username, password):
        """用户登录认证"""
        if username == USERNAME and password == PASSWORD:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.init_db()
            self.authenticated = True
            return True
        return False

    def init_db(self):
        """初始化数据库"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            fields TEXT NOT NULL
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
        ''')
        self.conn.commit()

    def create_template(self, name, fields):
        """创建模板"""
        if not self.authenticated:
            return False
        try:
            fields_json = json.dumps(fields)
            self.cursor.execute("INSERT INTO templates (name, fields) VALUES (?, ?)", (name, fields_json))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_templates(self):
        """列出所有模板"""
        if not self.authenticated:
            return []
        self.cursor.execute("SELECT id, name, fields FROM templates")
        return self.cursor.fetchall()

    def save_data(self, template_id, data):
        if not self.authenticated:
            return False, "Unauthorized access."
        self.cursor.execute("SELECT fields FROM templates WHERE id = ?", (template_id,))
        result = self.cursor.fetchone()
        if not result:
            return False, "模板未找到"
        fields = json.loads(result[0])
        if not all(field in data for field in fields):
            return False, "数据形式与模板不匹配"
        content = json.dumps(data)
        self.cursor.execute("INSERT INTO data (template_id, content) VALUES (?, ?)", (template_id, content))
        self.conn.commit()
        return True, "保存成功！"
    

    
    def search_data(self, template_id, **kwargs):
        """按模板 ID 和条件查询数据"""
        if not self.authenticated:
            return []
        self.cursor.execute("SELECT id, content, timestamp FROM data WHERE template_id = ?", (template_id,))
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            content = json.loads(row[1])
            if all(content.get(k) == v for k, v in kwargs.items()):
                results.append((row[0], content, row[2]))
        return results

    def close(self):
        """关闭数据库"""
        if self.conn:
            self.conn.close()


class InfoStorageGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数据存储系统v0.2")
        self.root.geometry("900x600")
        self.system = InfoStorageSystem()
        self.login_screen()

    def login_screen(self):
        """登录界面"""
        self.clear_screen()
        Label(self.root, text="Login", font=("Arial", 18)).pack(pady=10)

        Label(self.root, text="用户名:").pack()
        username_entry = Entry(self.root)
        username_entry.pack(pady=5)

        Label(self.root, text="密码:").pack()
        password_entry = Entry(self.root, show="*")
        password_entry.pack(pady=5)

        def attempt_login():
            username = username_entry.get()
            password = password_entry.get()
            if self.system.authenticate(username, password):
                self.home_screen()
            else:
                messagebox.showerror("登陆失败", "无效的用户名或密码")

        Button(self.root, text="登录", command=attempt_login).pack(pady=10)

    def home_screen(self):
        """主菜单"""
        self.clear_screen()
        Label(self.root, text=f"信息存储系统 (用户: {DB_OWNER})", font=("Arial", 18)).pack(pady=10)

        ttk.Button(self.root, text="Create Template", command=self.create_template_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="List Templates", command=self.list_templates_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Save Data", command=self.save_data_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Search Data", command=self.search_data_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Exit", command=self.root.quit, width=20).pack(pady=10)

    def create_template_screen(self):
        """创建模板界面"""
        self.clear_screen()
        Label(self.root, text="创建模板", font=("Arial", 16)).pack(pady=10)

        Label(self.root, text="模板名称:").pack()
        name_entry = ttk.Entry(self.root)
        name_entry.pack(pady=5)

        Label(self.root, text="Fields (comma-separated):").pack()
        fields_entry = ttk.Entry(self.root)
        fields_entry.pack(pady=5)

        def save_template():
            name = name_entry.get()
            fields = [field.strip() for field in fields_entry.get().split(",") if field.strip()]
            if not name or not fields:
                messagebox.showerror("Error", "Template name and fields cannot be empty.")
                return
            if self.system.create_template(name, fields):
                messagebox.showinfo("Success", "Template created successfully!")
                self.home_screen()
            else:
                messagebox.showerror("Error", "Template already exists or invalid input.")

        ttk.Button(self.root, text="Save", command=save_template).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()

    def list_templates_screen(self):
        """列出模板界面"""
        self.clear_screen()
        Label(self.root, text="Templates", font=("Arial", 16)).pack(pady=10)

        columns = ("ID", "Name", "Fields")
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for t in self.system.list_templates():
            tree.insert("", "end", values=(t[0], t[1], json.loads(t[2])))

        ttk.Button(self.root, text="Back", command=self.home_screen).pack(pady=10)

    def save_data_screen(self):
        self.clear_screen()
        Label(self.root, text="Save Data", font=("Arial", 16)).pack(pady=10)

        # Template ID selection
        Label(self.root, text="Template ID:").pack()
        template_id_entry = ttk.Entry(self.root)
        template_id_entry.pack(pady=5)

        # Frame to hold dynamic fields
        fields_frame = ttk.Frame(self.root)
        fields_frame.pack(pady=10)

        # Function to load template fields
        def load_template_fields():
            # Clear previous fields
            for widget in fields_frame.winfo_children():
                widget.destroy()

            try:
                template_id = int(template_id_entry.get())
                # Fetch template fields from the database
                templates = self.system.list_templates()
                template = next((t for t in templates if t[0] == template_id), None)
                if template:
                    fields = json.loads(template[2])  # Load fields from the template
                    field_inputs.clear()  # Clear old references
                    for field in fields:
                        Label(fields_frame, text=field).pack(anchor="w")
                        entry = ttk.Entry(fields_frame)
                        entry.pack(pady=2)
                        field_inputs[field] = entry
                    result_label.config(text=f"Fields loaded for template ID {template_id}", foreground="green")
                else:
                    result_label.config(text="Template not found.", foreground="red")
            except ValueError:
                result_label.config(text="Invalid Template ID.", foreground="red")

        # Button to load fields
        field_inputs = {}
        ttk.Button(self.root, text="Load Template Fields", command=load_template_fields).pack(pady=5)

        # Result label
        result_label = Label(self.root, text="")
        result_label.pack(pady=10)

        # Save data button
        def save_data():
            try:
                template_id = int(template_id_entry.get())
                data = {field: entry.get() for field, entry in field_inputs.items()}
                success, message = self.system.save_data(template_id, data)
                result_label.config(text=message, foreground="green" if success else "red")
            except ValueError:
                result_label.config(text="Invalid input or template ID.", foreground="red")

        ttk.Button(self.root, text="Save Data", command=save_data).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()
    
    def search_data_screen(self):
        """搜索数据界面"""
        self.clear_screen()
        Label(self.root, text="Search Data", font=("Arial", 16)).pack(pady=10)

        Label(self.root, text="Select Template:").pack()
        template_var = StringVar()
        template_dropdown = ttk.Combobox(self.root, textvariable=template_var, state="readonly")
        template_dropdown.pack(pady=5)

        templates = self.system.list_templates()
        template_dict = {t[1]: (t[0], json.loads(t[2])) for t in templates}
        template_dropdown["values"] = list(template_dict.keys())

        Label(self.root, text="Search Criteria (key=value, comma-separated):").pack()
        criteria_entry = ttk.Entry(self.root)
        criteria_entry.pack(pady=5)

        result_tree = None

        def search():
            nonlocal result_tree
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    widget.destroy()

            template_name = template_var.get()
            if not template_name:
                messagebox.showerror("Error", "Please select a template.")
                return

            template_id, fields = template_dict[template_name]
            columns = ["ID"] + fields + ["Timestamp"]

            result_tree = ttk.Treeview(self.root, columns=columns, show="headings")
            for col in columns:
                result_tree.heading(col, text=col)
                result_tree.column(col, width=100)

            result_tree.pack(fill="both", expand=True, padx=10, pady=10)

            try:
                criteria = dict(item.split("=") for item in criteria_entry.get().split(",") if "=" in item)
                results = self.system.search_data(template_id, **criteria)
                for r in results:
                    row_values = [r[0]] + [r[1].get(f, "") for f in fields] + [r[2]]
                    result_tree.insert("", "end", values=row_values)
            except ValueError:
                messagebox.showerror("Error", "Invalid search input.")

        ttk.Button(self.root, text="Search", command=search).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()

    def clear_screen(self):
        """清空界面"""
        for widget in self.root.winfo_children():
            widget.destroy()



if __name__ == "__main__":
    root = Tk()
    app = InfoStorageGUI(root)
    root.mainloop()
