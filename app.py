import os
import subprocess
import threading
import time
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
import sys
import sys

PLATFORM_OPTIONS = [
    'linux/amd64',
    'linux/amd64/v2',
    'linux/amd64/v3',
    'linux/amd64/v4',
    'linux/386',
    'linux/arm64',
    'linux/arm64/v8',
    'linux/arm/v7',
    'linux/arm/v6',
    'linux/arm/v5',
    'linux/ppc64le',
    'linux/s390x',
    'linux/mips64le',
    'linux/mips64',
    'linux/mipsle',
    'linux/mips',
    'linux/riscv64',
    'linux/loong64'
]

# 常见基础镜像(python/nginx/node等)通常支持的架构
# 不在此列表中的架构需要手动验证基础镜像是否支持
WIDELY_SUPPORTED_PLATFORMS = {
    'linux/amd64',
    'linux/arm64',
    'linux/arm/v7',
    'linux/arm/v6',
    'linux/386',
    'linux/ppc64le',
    'linux/s390x'
}


class BuildXApp:
    def __init__(self, root):
        self.root = root
        self.root.title('DockerAuto Builder - Docker Buildx GUI')
        self.root.geometry('1400x1200')
        self.root.resizable(True, True)

        self.build_thread = None
        self.running_process = None
        
        # 设置主题跟随系统
        self._setup_theme()

        self._create_widgets()
        self._refresh_docker_status()

    def _setup_theme(self):
        # 使用Win11风格主题
        self.root.configure(bg='#f0f0f0')
        
        # 使用vista主题（接近Win11风格）
        style = ttk.Style()
        style.theme_use('vista')
        
        # 设置合适的字体大小以支持高 DPI
        default_font = ('Microsoft YaHei UI', 10)
        self.root.option_add('*Font', default_font)
        
        # 自定义Win11风格样式
        style.configure('.', 
                       background='#f0f0f0',
                       foreground='#000000',
                       fieldbackground='#ffffff',
                       font=default_font)
        
        style.configure('TFrame', 
                       background='#f0f0f0')
        
        style.configure('TLabelFrame', 
                       background='#f0f0f0',
                       foreground='#000000',
                       bordercolor='#d0d0d0',
                       borderwidth=1,
                       font=('Microsoft YaHei UI', 11, 'bold'))
        
        style.configure('TLabelFrame.Label',
                       background='#f0f0f0',
                       foreground='#000000',
                       font=('Microsoft YaHei UI', 11, 'bold'))
        
        style.configure('TLabel', 
                       background='#f0f0f0',
                       foreground='#000000')
        
        style.configure('TButton', 
                       background='#e0e0e0',
                       foreground='#000000',
                       bordercolor='#d0d0d0',
                       borderwidth=1,
                       relief='flat')
        
        style.map('TButton',
                  background=[('active', '#d0d0d0'), ('pressed', '#c0c0c0')],
                  foreground=[('active', '#000000'), ('pressed', '#000000')])
        
        style.configure('TEntry', 
                       fieldbackground='#ffffff',
                       foreground='#000000',
                       bordercolor='#d0d0d0',
                       borderwidth=1,
                       relief='flat')
        
        style.configure('TCombobox', 
                       fieldbackground='#ffffff',
                       foreground='#000000',
                       background='#e0e0e0',
                       bordercolor='#d0d0d0', 
                       borderwidth=1,
                       relief='flat')
        
        style.configure('TCombobox.Listbox',
                       background='#ffffff',
                       foreground='#000000')
        style.configure('TCombobox.Listbox.Item',
                       background='#ffffff',
                       foreground='#000000')
        style.map('TCombobox.Listbox.Item',
                  background=[('selected', '#0078d4')],
                  foreground=[('selected', '#ffffff')])
        
        style.configure('Checkbutton', 
                       background='#f0f0f0',
                       foreground='#000000',
                       indicatorbackground='#ffffff',
                       indicatorcolor='#000000')
        
        style.map('Checkbutton',
                  indicatorcolor=[('selected', '#0078d4')],
                  background=[('active', '#e0e0e0')])

    def _is_dark_theme(self):
        # 检测系统主题
        if sys.platform == 'win32':
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except:
                return False
        elif sys.platform == 'darwin':
            try:
                from AppKit import NSUserDefaults
                defaults = NSUserDefaults.standardUserDefaults()
                return defaults.stringForKey_('AppleInterfaceStyle') == 'Dark'
            except:
                return False
        else:
            # Linux/Unix
            try:
                import subprocess
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], 
                                      capture_output=True, text=True)
                return 'dark' in result.stdout.lower()
            except:
                try:
                    result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                          capture_output=True, text=True)
                    return 'dark' in result.stdout.lower()
                except:
                    return False

    def _create_widgets(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=BOTH, expand=True)

        # Top status
        status_frame = ttk.LabelFrame(main, text='Docker 状态')
        status_frame.pack(fill=X, pady=(0, 10))
        self.status_var = StringVar(value='检查中...')
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(anchor=W, padx=10, pady=10)

        # Input fields
        input_frame = ttk.LabelFrame(main, text='构建配置')
        input_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(input_frame, text='项目目录').grid(row=0, column=0, sticky=W, padx=8, pady=6)
        self.project_var = StringVar()
        self.project_entry = ttk.Entry(input_frame, textvariable=self.project_var, width=80)
        self.project_entry.grid(row=0, column=1, padx=8, pady=6, sticky=EW)
        ttk.Button(input_frame, text='选择目录', command=self.choose_project_dir).grid(row=0, column=2, padx=6, pady=6)

        ttk.Label(input_frame, text='Dockerfile').grid(row=1, column=0, sticky=W, padx=8, pady=6)
        self.dockerfile_var = StringVar(value='Dockerfile')
        self.dockerfile_combobox = ttk.Combobox(input_frame, textvariable=self.dockerfile_var, width=78, state='readonly')
        self.dockerfile_combobox.grid(row=1, column=1, padx=8, pady=6, sticky=EW)
        ttk.Button(input_frame, text='查找Dockerfile', command=self.find_dockerfiles).grid(row=1, column=2, padx=6, pady=6)

        ttk.Label(input_frame, text='镜像名称').grid(row=2, column=0, sticky=W, padx=8, pady=6)
        self.image_name_var = StringVar()
        ttk.Entry(input_frame, textvariable=self.image_name_var, width=40).grid(row=2, column=1, padx=8, pady=6, sticky=EW)

        ttk.Label(input_frame, text='版本号').grid(row=2, column=2, sticky=W, padx=8, pady=6)
        self.image_tag_var = StringVar()
        ttk.Entry(input_frame, textvariable=self.image_tag_var, width=20).grid(row=2, column=3, padx=8, pady=6, sticky=EW)

        ttk.Label(input_frame, text='仓库地址').grid(row=3, column=0, sticky=W, padx=8, pady=6)
        self.registry_var = StringVar(value='ghcr.io')
        self.registry_combobox = ttk.Combobox(input_frame, textvariable=self.registry_var, width=38, state='readonly')
        self.registry_combobox['values'] = ('ghcr.io', 'docker.io', '自定义')
        self.registry_combobox.grid(row=3, column=1, padx=8, pady=6, sticky=EW)
        self.registry_combobox.bind('<<ComboboxSelected>>', self.on_registry_change)
        self.custom_registry_var = StringVar()
        self.custom_registry_entry = ttk.Entry(input_frame, textvariable=self.custom_registry_var, width=38)

        ttk.Label(input_frame, text='用户名').grid(row=3, column=2, sticky=W, padx=8, pady=6)
        self.registry_user_var = StringVar()
        self.registry_user_entry = ttk.Entry(input_frame, textvariable=self.registry_user_var, width=20)
        self.registry_user_entry.grid(row=3, column=3, padx=8, pady=6, sticky=EW)

        self.token_label = ttk.Label(input_frame, text='Token')
        self.token_label.grid(row=4, column=0, sticky=W, padx=8, pady=6)
        self.token_var = StringVar()
        self.token_entry = ttk.Entry(input_frame, textvariable=self.token_var, show='*', width=80)
        self.token_entry.grid(row=4, column=1, padx=8, pady=6, sticky=EW)

        self.password_label = ttk.Label(input_frame, text='密码')
        self.password_var = StringVar()
        self.password_entry = ttk.Entry(input_frame, textvariable=self.password_var, show='*', width=80)

        ttk.Button(input_frame, text='登录仓库', command=self.login_registry).grid(row=4, column=2, padx=6, pady=6)
        self.on_registry_change()

        ttk.Label(input_frame, text='构建参数').grid(row=5, column=0, sticky=W, padx=8, pady=6)
        self.build_args_var = StringVar()
        ttk.Entry(input_frame, textvariable=self.build_args_var, width=80).grid(row=5, column=1, padx=8, pady=6, sticky=EW)

        ttk.Label(input_frame, text='平台').grid(row=6, column=0, sticky=NW, padx=8, pady=6)
        self.platform_vars = {}
        # 使用支持自动换行的容器
        platform_frame = ttk.Frame(input_frame)
        platform_frame.grid(row=6, column=1, columnspan=3, sticky=EW, padx=8, pady=6)
        
        # 快捷操作按钮
        quick_buttons_frame = ttk.Frame(platform_frame)
        quick_buttons_frame.grid(row=0, column=0, columnspan=5, sticky=W, padx=0, pady=(0, 8))
        ttk.Button(quick_buttons_frame, text='选择常见平台', command=self.select_common_platforms).pack(side=LEFT, padx=3)
        ttk.Button(quick_buttons_frame, text='全选', command=self.select_all_platforms).pack(side=LEFT, padx=3)
        ttk.Button(quick_buttons_frame, text='清空选择', command=self.clear_platforms).pack(side=LEFT, padx=3)
        
        # 每行显示的平台数量，超过自动换行
        columns_per_row = 5
        for i, platform in enumerate(PLATFORM_OPTIONS):
            var = BooleanVar(value=(platform == 'linux/amd64'))
            self.platform_vars[platform] = var
            row = (i // columns_per_row) + 1  # 留出第0行给快捷按钮
            col = i % columns_per_row
            ttk.Checkbutton(platform_frame, text=platform, variable=var).grid(
                row=row, column=col, sticky=W, padx=4, pady=3
            )

        self.push_var = BooleanVar()
        ttk.Checkbutton(input_frame, text='构建后推送到仓库', variable=self.push_var).grid(row=7, column=1, sticky=W, padx=8, pady=6)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=8, column=0, columnspan=4, sticky=EW, padx=8, pady=8)
        ttk.Button(button_frame, text='开始构建', command=self.start_build).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text='停止构建', command=self.stop_build).pack(side=LEFT, padx=5)

        input_frame.columnconfigure(1, weight=1)

        # Command preview
        preview_frame = ttk.LabelFrame(main, text='构建命令')
        preview_frame.pack(fill=X, pady=(0, 10))
        self.command_text = scrolledtext.ScrolledText(preview_frame, height=5, wrap=WORD)
        # Win11风格样式
        self.command_text.configure(bg='#ffffff', fg='#000000', insertbackground='#000000', bd=1, relief='solid', highlightbackground='#d0d0d0', highlightcolor='#d0d0d0')
        self.command_text.pack(fill=X, padx=8, pady=8)

        # Log output
        log_frame = ttk.LabelFrame(main, text='构建日志')
        log_frame.pack(fill=BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=WORD)
        # Win11风格样式
        self.log_text.configure(bg='#ffffff', fg='#000000', insertbackground='#000000', bd=1, relief='solid', highlightbackground='#d0d0d0', highlightcolor='#d0d0d0')
        self.log_text.pack(fill=BOTH, expand=True, padx=8, pady=8)

    def choose_project_dir(self):
        folder = filedialog.askdirectory(title='选择项目目录')
        if folder:
            self.project_var.set(folder)
            self.find_dockerfiles()

    def find_dockerfiles(self):
        project_dir = self.project_var.get().strip()
        if not project_dir or not os.path.isdir(project_dir):
            messagebox.showwarning('提示', '请先选择有效的项目目录')
            return
        
        dockerfiles = []
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.lower() == 'dockerfile':
                    rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                    dockerfiles.append(rel_path)
        
        if dockerfiles:
            self.dockerfile_combobox['values'] = dockerfiles
            if self.dockerfile_var.get() not in dockerfiles:
                self.dockerfile_var.set(dockerfiles[0])
        else:
            self.dockerfile_combobox['values'] = ()
            messagebox.showinfo('提示', '未找到Dockerfile')

    def select_common_platforms(self):
        # 选择常见平台（python/nginx等官方镜像通常支持的架构）
        for platform, var in self.platform_vars.items():
            var.set(platform in WIDELY_SUPPORTED_PLATFORMS)

    def select_all_platforms(self):
        # 全选所有平台
        for var in self.platform_vars.values():
            var.set(True)

    def clear_platforms(self):
        # 清空所有选择
        for var in self.platform_vars.values():
            var.set(False)

    def _refresh_docker_status(self):
        def worker():
            while True:
                status = self._check_docker_status()
                self.root.after(0, lambda s=status: self.status_var.set(s))
                time.sleep(3)

        threading.Thread(target=worker, daemon=True).start()

    def _check_docker_status(self):
        try:
            if sys.platform == 'win32':
                # Windows 平台不显示命令行窗口
                docker_info = subprocess.run(
                    ['docker', 'info'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                buildx_info = subprocess.run(
                    ['docker', 'buildx', 'version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux 平台正常调用
                docker_info = subprocess.run(
                    ['docker', 'info'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                buildx_info = subprocess.run(
                    ['docker', 'buildx', 'version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            if docker_info.returncode != 0:
                message = docker_info.stderr.strip() or docker_info.stdout.strip() or 'Docker daemon 未启动'
                return f'❌ {message}'
            if buildx_info.returncode != 0:
                message = buildx_info.stderr.strip() or buildx_info.stdout.strip() or 'buildx 不可用'
                return f'❌ {message}'
            return '✅ Docker 可用，buildx 正常'
        except FileNotFoundError:
            return '❌ 未找到 docker 命令'
        except Exception as e:
            return f'❌ {e}'

    def _append_log(self, text):
        self.log_text.insert(END, text + '\n')
        self.log_text.see(END)

    def on_registry_change(self, event=None):
        registry = self.registry_var.get()
        if registry == '自定义':
            self.registry_combobox.grid_forget()
            self.custom_registry_entry.grid(row=3, column=1, padx=8, pady=6, sticky=EW)
        else:
            self.custom_registry_entry.grid_forget()
            self.registry_combobox.grid(row=3, column=1, padx=8, pady=6, sticky=EW)
        
        if registry == 'ghcr.io':
            self.token_label.grid(row=4, column=0, sticky=W, padx=8, pady=6)
            self.token_entry.grid(row=4, column=1, padx=8, pady=6, sticky=EW)
            self.password_label.grid_forget()
            self.password_entry.grid_forget()
        else:
            self.password_label.grid(row=4, column=0, sticky=W, padx=8, pady=6)
            self.password_entry.grid(row=4, column=1, padx=8, pady=6, sticky=EW)
            self.token_label.grid_forget()
            self.token_entry.grid_forget()

    def login_registry(self):
        registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()
        username = self.registry_user_var.get().strip()
        
        if not registry:
            messagebox.showerror('错误', '请填写仓库地址')
            return
            
        if self.registry_var.get() == 'ghcr.io':
            token = self.token_var.get().strip()
            if not username or not token:
                messagebox.showerror('错误', '请先填写用户名和Token')
                return
            auth_data = token
        else:
            password = self.password_var.get().strip()
            if not username or not password:
                messagebox.showerror('错误', '请先填写用户名和密码')
                return
            auth_data = password

        try:
            cmd = ['docker', 'login', registry, '-u', username, '--password-stdin']
            if sys.platform == 'win32':
                # Windows 平台不显示命令行窗口
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux 平台正常调用
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            stdout, _ = process.communicate(input=auth_data)
            if process.returncode == 0:
                messagebox.showinfo('成功', f'已登录到 {registry}')
                self._append_log(f'登录成功: {registry}')
            else:
                messagebox.showerror('登录失败', stdout.strip())
                self._append_log(f'登录失败: {stdout.strip()}')
        except Exception as e:
            messagebox.showerror('错误', str(e))

    def _build_command(self):
        project_dir = self.project_var.get().strip()
        dockerfile = self.dockerfile_var.get().strip() or 'Dockerfile'
        image_name = self.image_name_var.get().strip()
        image_tag = self.image_tag_var.get().strip()
        build_args = self.build_args_var.get().strip()
        push = self.push_var.get()
        registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()

        if not project_dir or not os.path.isdir(project_dir):
            raise ValueError('请选择有效的项目目录')
        if not image_name:
            raise ValueError('请输入镜像名称')

        selected_platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        if not selected_platforms:
            raise ValueError('请至少选择一个平台')

        project_path = Path(project_dir)
        dockerfile_path = project_path / dockerfile
        if not dockerfile_path.is_file():
            # 如果指定的Dockerfile不存在，尝试查找目录下的Dockerfile
            found_dockerfiles = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.lower() == 'dockerfile':
                        found_dockerfiles.append(os.path.relpath(os.path.join(root, file), project_path))
            if found_dockerfiles:
                raise ValueError(f'Dockerfile 不存在: {dockerfile_path}\n找到以下Dockerfile: {", ".join(found_dockerfiles)}')
            else:
                raise ValueError(f'Dockerfile 不存在: {dockerfile_path}')

        if len(selected_platforms) > 1 and not push:
            raise ValueError('如果不推送，建议只选择一个平台；buildx 的 --load 仅适合单平台构建')
        
        # 检查推送时的登录状态
        if push:
            registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()
            username = self.registry_user_var.get().strip()
            
            if not registry:
                raise ValueError('请填写仓库地址')
            if not username:
                raise ValueError('请填写用户名')
            
            if self.registry_var.get() == 'ghcr.io':
                token = self.token_var.get().strip()
                if not token:
                    # 不在这里验证，留到start_build中处理
                    pass
            else:
                password = self.password_var.get().strip()
                if not password:
                    # 不在这里验证，留到start_build中处理
                    pass

        username = self.registry_user_var.get().strip()
        
        # 构建latest标签的镜像
        latest_image = f'{image_name}:latest'
        if registry and registry != 'docker.io':
            if registry == 'ghcr.io' and username:
                latest_image = f'{registry}/{username}/{image_name}:latest'
            else:
                latest_image = f'{registry}/{image_name}:latest'

        cmd = ['docker', 'buildx', 'build']
        cmd.extend(['--platform', ','.join(selected_platforms)])
        cmd.extend(['-f', str(dockerfile_path)])
        cmd.extend(['-t', latest_image])
        
        # 如果填写了版本号，添加版本号标签
        if image_tag:
            version_image = f'{image_name}:{image_tag}'
            if registry and registry != 'docker.io':
                if registry == 'ghcr.io' and username:
                    version_image = f'{registry}/{username}/{image_name}:{image_tag}'
                else:
                    version_image = f'{registry}/{image_name}:{image_tag}'
            cmd.extend(['-t', version_image])
        if push:
            cmd.append('--push')
        else:
            cmd.append('--load')
        if build_args:
            for arg in [item.strip() for item in build_args.split(',') if item.strip()]:
                cmd.extend(['--build-arg', arg])
        cmd.append(str(project_path))
        return cmd, project_path

    def start_build(self):
        if self.build_thread and self.build_thread.is_alive():
            messagebox.showinfo('提示', '构建任务已经在运行中')
            return

        try:
            # 检查是否需要推送且未登录
            push = self.push_var.get()
            registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()
            username = self.registry_user_var.get().strip()
            
            if push and registry and username:
                # 检查是否已登录
                logged_in = self._check_registry_login(registry, username)
                if not logged_in:
                    # 尝试自动登录
                    login_success = self._auto_login_registry()
                    if not login_success:
                        # 显示登录弹窗
                        login_success = self.show_login_dialog()
                        if not login_success:
                            messagebox.showinfo('提示', '登录已取消，构建终止')
                            return
            
            cmd, project_path = self._build_command()
            self.command_text.delete('1.0', END)
            self.command_text.insert(END, ' '.join(cmd))
            self.log_text.delete('1.0', END)
            self._append_log('开始构建...')
            self._append_log(f'命令: {" ".join(cmd)}')

            if sys.platform == 'win32':
                # Windows 平台不显示命令行窗口
                self.running_process = subprocess.Popen(
                    cmd,
                    cwd=str(project_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux 平台正常调用
                self.running_process = subprocess.Popen(
                    cmd,
                    cwd=str(project_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )

            def worker():
                try:
                    for line in self.running_process.stdout:
                        if line:
                            self.root.after(0, lambda text=line.rstrip('\n'): self._append_log(text))
                    returncode = self.running_process.wait()
                    if returncode == 0:
                        self.root.after(0, lambda: self._append_log('构建成功完成'))
                    else:
                        self.root.after(0, lambda: self._append_log(f'构建失败，退出码: {returncode}'))
                except Exception as e:
                    self.root.after(0, lambda: self._append_log(f'运行异常: {e}'))
                finally:
                    self.root.after(0, lambda: self._update_build_state(False))

            self._update_build_state(True)
            self.build_thread = threading.Thread(target=worker, daemon=True)
            self.build_thread.start()
        except ValueError as e:
            messagebox.showerror('参数错误', str(e))

    def _check_registry_login(self, registry, username):
        try:
            # 检查是否已登录到仓库
            cmd = ['docker', 'login', '--get-login', registry]
            if sys.platform == 'win32':
                # Windows 平台不显示命令行窗口
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux 平台正常调用
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            if result.returncode == 0:
                logged_in_user = result.stdout.strip()
                return logged_in_user == username
            return False
        except Exception:
            return False

    def _auto_login_registry(self):
        try:
            registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()
            username = self.registry_user_var.get().strip()
            
            if not registry or not username:
                return False
                
            if self.registry_var.get() == 'ghcr.io':
                token = self.token_var.get().strip()
                if not token:
                    return False
                auth_data = token
            else:
                password = self.password_var.get().strip()
                if not password:
                    return False
                auth_data = password
            
            cmd = ['docker', 'login', registry, '-u', username, '--password-stdin']
            if sys.platform == 'win32':
                # Windows 平台不显示命令行窗口
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux 平台正常调用
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            stdout, _ = process.communicate(input=auth_data)
            if process.returncode == 0:
                self._append_log(f'自动登录成功: {registry}')
                return True
            else:
                self._append_log(f'自动登录失败: {stdout.strip()}')
                return False
        except Exception as e:
            self._append_log(f'自动登录异常: {str(e)}')
            return False

    def show_login_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title('登录仓库')
        dialog.geometry('400x250')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.bg_color)
        dialog.configure(bg=self.bg_color)
        
        login_success = False
        
        ttk.Label(dialog, text='用户名:').grid(row=0, column=0, sticky=W, padx=20, pady=20)
        user_var = StringVar(value=self.registry_user_var.get())
        user_entry = ttk.Entry(dialog, textvariable=user_var, width=30)
        user_entry.grid(row=0, column=1, padx=20, pady=20)
        
        if self.registry_var.get() == 'ghcr.io':
            ttk.Label(dialog, text='Token:').grid(row=1, column=0, sticky=W, padx=20, pady=5)
            pass_var = StringVar(value=self.token_var.get())
            pass_entry = ttk.Entry(dialog, textvariable=pass_var, show='*', width=30)
            pass_entry.grid(row=1, column=1, padx=20, pady=5)
        else:
            ttk.Label(dialog, text='密码:').grid(row=1, column=0, sticky=W, padx=20, pady=5)
            pass_var = StringVar(value=self.password_var.get())
            pass_entry = ttk.Entry(dialog, textvariable=pass_var, show='*', width=30)
            pass_entry.grid(row=1, column=1, padx=20, pady=5)
        
        def on_login():
            nonlocal login_success
            registry = self.custom_registry_var.get().strip() if self.registry_var.get() == '自定义' else self.registry_var.get().strip()
            username = user_var.get().strip()
            auth_data = pass_var.get().strip()
            
            if not username or not auth_data:
                messagebox.showerror('错误', '请填写用户名和密码/Token')
                return
            
            try:
                cmd = ['docker', 'login', registry, '-u', username, '--password-stdin']
                if sys.platform == 'win32':
                    # Windows 平台不显示命令行窗口
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Linux 平台正常调用
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                stdout, _ = process.communicate(input=auth_data)
                if process.returncode == 0:
                    messagebox.showinfo('成功', f'已登录到 {registry}')
                    self._append_log(f'登录成功: {registry}')
                    # 更新主窗口的登录信息
                    self.registry_user_var.set(username)
                    if self.registry_var.get() == 'ghcr.io':
                        self.token_var.set(auth_data)
                    else:
                        self.password_var.set(auth_data)
                    login_success = True
                    dialog.destroy()
                else:
                    messagebox.showerror('登录失败', stdout.strip())
                    self._append_log(f'登录失败: {stdout.strip()}')
            except Exception as e:
                messagebox.showerror('错误', str(e))
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text='登录', command=on_login).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=on_cancel).pack(side=LEFT, padx=10)
        
        dialog.wait_window()
        return login_success

    def stop_build(self):
        if self.running_process and self.running_process.poll() is None:
            self.running_process.terminate()
            self._append_log('已发送停止信号')

    def _update_build_state(self, running):
        pass


if __name__ == '__main__':
    # Windows 平台启用高 DPI 支持
    if sys.platform == 'win32':
        try:
            import ctypes
            # 启用 per-monitor DPI 感知（Windows 8.1 及以上）
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                # 旧版 Windows 使用 SetProcessDPIAware
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    
    # 配置 Tkinter 以支持高 DPI
    root = Tk()
    root.title('Docker BuildX 构建工具')
    
    # 根据屏幕分辨率自动计算窗口尺寸
    # 获取屏幕实际分辨率（考虑 DPI 缩放）
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # 直接使用屏幕百分比，更直观可靠
    # 宽度 = 屏幕宽度的 30% (约等于 1/3)
    # 高度 = 屏幕高度的 75%（更高，便于显示构建日志）
    window_width = int(screen_width * 0.30)
    window_height = int(screen_height * 0.75)
    
    # 合理的最小尺寸（确保控件不拥挤）
    min_width = 1200
    min_height = 1200
    window_width = max(window_width, min_width)
    window_height = max(window_height, min_height)
    
    # 最大尺寸（不超过屏幕的 90%）
    max_width = int(screen_width * 0.9)
    max_height = int(screen_height * 0.9)
    window_width = min(window_width, max_width)
    window_height = min(window_height, max_height)
    
    # 计算窗口居中位置
    x_position = int((screen_width - window_width) / 2)
    y_position = int((screen_height - window_height) / 2)
    
    # 设置窗口尺寸和位置：宽x高+X坐标+Y坐标
    geometry_str = f'{window_width}x{window_height}+{x_position}+{y_position}'
    print(f'屏幕分辨率: {screen_width}x{screen_height}')
    print(f'窗口尺寸: {window_width}x{window_height}')
    print(f'窗口位置: ({x_position}, {y_position})')
    print(f'应用几何设置: {geometry_str}')
    
    root.geometry(geometry_str)
    
    # 强制更新窗口
    root.update()
    
    # 验证实际窗口尺寸
    actual_width = root.winfo_width()
    actual_height = root.winfo_height()
    print(f'实际窗口尺寸: {actual_width}x{actual_height}')
    
    # 设置最小窗口尺寸，防止过小
    root.minsize(min_width, min_height)
    
    app = BuildXApp(root)
    root.mainloop()