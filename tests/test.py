import sqlite3
import json
from tkinter import Tk, Label, Entry, Button, Text, Listbox, END, Toplevel, Scrollbar, StringVar, ttk





class InfoStorageSystem:
    def __init__(self, db_name="info_system.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
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
        try:
            fields_json = json.dumps(fields)
            self.cursor.execute(
                "INSERT INTO templates (name, fields) VALUES (?, ?)", (name, fields_json)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_templates(self):
        self.cursor.execute("SELECT id, name, fields FROM templates")
        return self.cursor.fetchall()

    def save_data(self, template_id, data):
        self.cursor.execute("SELECT fields FROM templates WHERE id = ?", (template_id,))
        result = self.cursor.fetchone()
        if not result:
            return False, "Template not found."
        fields = json.loads(result[0])
        if not all(field in data for field in fields):
            return False, "Data does not match template fields."
        content = json.dumps(data)
        self.cursor.execute(
            "INSERT INTO data (template_id, content) VALUES (?, ?)",
            (template_id, content),
        )
        self.conn.commit()
        return True, "Data saved successfully."

    def search_data(self, template_id, **kwargs):
        self.cursor.execute("SELECT fields FROM templates WHERE id = ?", (template_id,))
        result = self.cursor.fetchone()
        if not result:
            return []
        fields = json.loads(result[0])
        self.cursor.execute(
            "SELECT id, content, timestamp FROM data WHERE template_id = ?",
            (template_id,),
        )
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            content = json.loads(row[1])
            if all(content.get(k) == v for k, v in kwargs.items()):
                results.append((row[0], content, row[2]))
        return results

    def analyze_data(self, template_id):
        self.cursor.execute("SELECT fields FROM templates WHERE id = ?", (template_id,))
        result = self.cursor.fetchone()
        if not result:
            return {}
        fields = json.loads(result[0])
        self.cursor.execute(
            "SELECT content FROM data WHERE template_id = ?", (template_id,)
        )
        rows = self.cursor.fetchall()
        data_list = [json.loads(row[0]) for row in rows]

        analysis = {}
        for field in fields:
            values = [d[field] for d in data_list if field in d]
            if all(isinstance(v, (int, float)) for v in values):
                analysis[field] = {
                    "Sum": sum(values),
                    "Average": sum(values) / len(values) if values else 0,
                }
            else:
                analysis[field] = {"Unique Values": set(values)}
        return analysis

    def close(self):
        self.conn.close()


class InfoStorageGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Info Storage System")
        self.root.geometry("600x400")
        self.system = InfoStorageSystem()

        # Theme
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Home Screen
        self.home_screen()

    def home_screen(self):
        self.clear_screen()
        Label(self.root, text="Info Storage System", font=("Arial", 18)).pack(pady=10)

        ttk.Button(self.root, text="Create Template", command=self.create_template_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="List Templates", command=self.list_templates_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Save Data", command=self.save_data_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Search Data", command=self.search_data_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Analyze Data", command=self.analyze_data_screen, width=20).pack(pady=5)
        ttk.Button(self.root, text="Exit", command=self.root.quit, width=20).pack(pady=10)

    def create_template_screen(self):
        self.clear_screen()
        Label(self.root, text="Create Template", font=("Arial", 16)).pack(pady=10)

        Label(self.root, text="Template Name:").pack()
        name_entry = ttk.Entry(self.root)
        name_entry.pack(pady=5)

        field_frame = ttk.Frame(self.root)
        field_frame.pack(pady=10)
        Label(field_frame, text="Fields:").grid(row=0, column=0)

        fields_list = Listbox(field_frame, height=5, width=30)
        fields_list.grid(row=0, column=1, padx=5)
        scrollbar = ttk.Scrollbar(field_frame, orient="vertical", command=fields_list.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        fields_list.config(yscrollcommand=scrollbar.set)

        add_field_entry = ttk.Entry(field_frame, width=20)
        add_field_entry.grid(row=1, column=1)

        def add_field():
            field = add_field_entry.get()
            if field:
                fields_list.insert(END, field)
                add_field_entry.delete(0, END)

        def remove_field():
            selected = fields_list.curselection()
            if selected:
                fields_list.delete(selected)

        ttk.Button(field_frame, text="Add Field", command=add_field).grid(row=1, column=0)
        ttk.Button(field_frame, text="Remove Field", command=remove_field).grid(row=2, column=0)

        def save_template():
            name = name_entry.get()
            fields = fields_list.get(0, END)
            if self.system.create_template(name, fields):
                Label(self.root, text="Template created successfully!", fg="green").pack()
            else:
                Label(self.root, text="Template already exists.", fg="red").pack()

        ttk.Button(self.root, text="Save Template", command=save_template).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()

    def list_templates_screen(self):
        self.clear_screen()
        Label(self.root, text="Templates", font=("Arial", 16)).pack(pady=10)
        templates = self.system.list_templates()
        for t in templates:
            Label(self.root, text=f"ID: {t[0]}, Name: {t[1]}, Fields: {json.loads(t[2])}").pack()
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
        self.clear_screen()
        Label(self.root, text="Search Data", font=("Arial", 16)).pack(pady=10)

        Label(self.root, text="Template ID:").pack()
        template_id_entry = ttk.Entry(self.root)
        template_id_entry.pack(pady=5)

        Label(self.root, text="Criteria (key=value, comma-separated):").pack()
        criteria_entry = ttk.Entry(self.root)
        criteria_entry.pack(pady=5)

        results_frame = ttk.Frame(self.root)
        results_frame.pack(pady=10)

        def search_data():
            try:
                template_id = int(template_id_entry.get())
                criteria = dict(item.split("=") for item in criteria_entry.get().split(",") if "=" in item)
                results = self.system.search_data(template_id, **criteria)
                for widget in results_frame.winfo_children():
                    widget.destroy()
                if results:
                    for r in results:
                        ttk.Label(results_frame, text=f"ID: {r[0]}, Content: {r[1]}, Timestamp: {r[2]}").pack(anchor="w")
                else:
                    ttk.Label(results_frame, text="No results found.").pack()
            except ValueError:
                ttk.Label(results_frame, text="Invalid criteria format.", foreground="red").pack()

        ttk.Button(self.root, text="Search", command=search_data).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()

    def analyze_data_screen(self):
        self.clear_screen()
        Label(self.root, text="Analyze Data", font=("Arial", 16)).pack(pady=10)

        Label(self.root, text="Template ID:").pack()
        template_id_entry = ttk.Entry(self.root)
        template_id_entry.pack(pady=5)

        results_frame = ttk.Frame(self.root)
        results_frame.pack(pady=10)

        def analyze_data():
            try:
                template_id = int(template_id_entry.get())
                analysis = self.system.analyze_data(template_id)
                for widget in results_frame.winfo_children():
                    widget.destroy()
                if analysis:
                    for field, stats in analysis.items():
                        ttk.Label(results_frame, text=f"Field: {field}, Stats: {stats}").pack(anchor="w")
                else:
                    ttk.Label(results_frame, text="No data found.").pack()
            except ValueError:
                ttk.Label(results_frame, text="Invalid Template ID.", foreground="red").pack()

        ttk.Button(self.root, text="Analyze", command=analyze_data).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.home_screen).pack()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()



    
    
if __name__ == "__main__":
    root = Tk()
    app = InfoStorageGUI(root)
    root.mainloop()
