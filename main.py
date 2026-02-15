import os
import sys
import time
import platform
import subprocess
import speedtest
from ping3 import ping
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint
from rich.columns import Columns

console = Console()


class NetworkMasterPro:
    def __init__(self):
        self.st = None

        # --- БАЗА СЕРВЕРОВ (Не удалять!) ---
        self.targets_kz = {
            "Almaty (Kazakhtelecom)": "kznic.kz",
            "Astana (Nazarbayev Univ)": "nu.edu.kz",
            "Karaganda (ISP)": "idnet.kz",
            "Aktau (Caspian)": "aktau.kz",
            "Beeline KZ": "beeline.kz"
        }

        self.targets_world = {
            # Европа
            "Amsterdam (NL)": "speedtest.ams-ix.net",
            "London (UK)": "bbc.co.uk",
            "Paris (France)": "orange.fr",
            "Frankfurt (Germany)": "de-cix.net",
            "Stockholm (Sweden)": "sunet.se",
            "Helsinki (Finland)": "ficix.fi",
            "Warsaw (Poland)": "onet.pl",
            "Vienna (Austria)": "univie.ac.at",
            "Madrid (Spain)": "rediris.es",

            # СНГ
            "Moscow (Russia)": "ya.ru",
            "Orenburg (Russia)": "mail.ru",

            # Азия
            "Dubai (UAE)": "du.ae",
            "Singapore": "nus.edu.sg",
            "Hong Kong": "hku.hk",
            "Tokyo (Japan)": "wide.ad.jp",
            "Seoul (Korea)": "kt.com",

            # Америка
            "New York (US East)": "nytimes.com",
            "Los Angeles (US West)": "ucla.edu",
            "San Jose (Silicon Valley)": "stanford.edu",
            "Mexico City": "unam.mx",
            "Sao Paulo (Brazil)": "uol.com.br"
        }

        self.all_targets = {**self.targets_kz, **self.targets_world}

    # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
    def open_file(self, path):
        """Открывает файл в зависимости от ОС"""
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(('open', path))
            else:
                subprocess.call(('xdg-open', path))
        except:
            pass

    def init_speedtest(self):
        console.print("[dim]Подключение к Speedtest API...[/dim]")
        try:
            self.st = speedtest.Speedtest(secure=True)
            return True
        except:
            console.print("[bold red]Ошибка подключения к Speedtest![/bold red]")
            return False

    # --- 1. КАРТА ПИНГОВ (SNAPSHOT) ---
    def run_ping_map(self):
        console.print(Panel("[bold yellow]ГЛОБАЛЬНАЯ КАРТА ПИНГОВ[/bold yellow]", expand=False))
        results = {}

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn()) as p:
            task = p.add_task("Сканирование...", total=len(self.all_targets))
            for name, host in self.all_targets.items():
                try:
                    res = ping(host, unit='ms', timeout=1.0)
                    results[name] = round(res, 1) if res else 999
                except:
                    results[name] = 999
                p.advance(task)

        # Рисуем
        self._draw_bar_chart(results, "Global Ping Map", "ping_map.png")
        self.open_file("ping_map.png")

    # --- 2. МОНИТОР ПИНГА (LIVE GRAPH) ---
    def run_ping_monitor(self):
        # 1. Выбор сервера
        console.print("\n[bold cyan]ВЫБОР СЕРВЕРА ДЛЯ ОТСЛЕЖИВАНИЯ:[/bold cyan]")
        servers_list = list(self.all_targets.keys())

        # Вывод списка в 2 колонки
        table = Table(show_header=False, box=None)
        table.add_column("ID", style="magenta", justify="right")
        table.add_column("Name", style="white")
        table.add_column("ID", style="magenta", justify="right")
        table.add_column("Name", style="white")

        for i in range(0, len(servers_list), 2):
            s1 = servers_list[i]
            s2 = servers_list[i + 1] if i + 1 < len(servers_list) else ""
            idx2 = str(i + 2) if s2 else ""
            table.add_row(str(i + 1), s1, idx2, s2)
        console.print(table)

        try:
            choice = IntPrompt.ask("Введите номер сервера", default=1)
            target_name = servers_list[choice - 1]
            target_host = self.all_targets[target_name]
        except:
            console.print("[red]Неверный выбор![/red]")
            return

        duration = IntPrompt.ask("Сколько секунд отслеживать?", default=10)

        # 2. Цикл замера
        console.print(f"\n[bold yellow]Мониторинг {target_name} ({target_host}) на {duration} сек...[/bold yellow]")

        x_time = []
        y_ping = []
        start_time = time.time()

        with Progress(SpinnerColumn(), TextColumn("[bold green]Ping... {task.fields[val]} ms"), BarColumn()) as p:
            task = p.add_task("Monitoring", total=duration, val="--")

            while (time.time() - start_time) < duration:
                current_t = round(time.time() - start_time, 1)
                try:
                    res = ping(target_host, unit='ms', timeout=1.0)
                    val = round(res, 1) if res else 0
                except:
                    val = 0

                x_time.append(current_t)
                y_ping.append(val)

                p.update(task, advance=(time.time() - start_time) - current_t, val=str(val))
                time.sleep(0.5)  # Интервал опроса

                # Костыль для плавного заполнения прогрессбара по времени
                if current_t > p.tasks[0].completed:
                    p.update(task, completed=current_t)

        # 3. График
        filename = "monitor_ping.png"
        self._draw_line_chart(x_time, y_ping, f"Ping Monitor: {target_name}", "Time (sec)", "Latency (ms)", filename)
        self.open_file(filename)

    # --- 3. СТАБИЛЬНОСТЬ СКОРОСТИ (SPEED MONITOR) ---
    def run_speed_monitor(self):
        if not self.init_speedtest(): return

        console.print("\n[bold cyan]ТЕСТ СТАБИЛЬНОСТИ СКОРОСТИ[/bold cyan]")
        console.print("[dim]Будет выполнено несколько замеров подряд для построения графика...[/dim]")

        iterations = IntPrompt.ask("Количество прогонов (рекомендуется 3-5)", default=3)

        # Выбираем сервер один раз
        console.print("[yellow]Поиск сервера...[/yellow]")
        self.st.get_best_server()
        srv_name = self.st.results.server['sponsor']

        dl_results = []
        ul_results = []
        x_runs = []

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn()) as p:
            task_total = p.add_task("[magenta]Общий прогресс...", total=iterations)

            for i in range(iterations):
                x_runs.append(i + 1)

                # DL
                p.update(task_total, description=f"Run {i + 1}/{iterations}: Downloading...")
                dl = self.st.download() / 1_000_000
                dl_results.append(round(dl, 2))

                # UL
                p.update(task_total, description=f"Run {i + 1}/{iterations}: Uploading...")
                ul = self.st.upload() / 1_000_000
                ul_results.append(round(ul, 2))

                p.advance(task_total)

        # Таблица текстом
        t = Table(title="Stability Data")
        t.add_column("Run #");
        t.add_column("Download");
        t.add_column("Upload")
        for i in range(iterations):
            t.add_row(str(i + 1), f"{dl_results[i]} Mbps", f"{ul_results[i]} Mbps")
        console.print(t)

        # Рисуем график
        filename = "monitor_speed.png"
        self._draw_dual_line_chart(x_runs, dl_results, ul_results, f"Speed Stability ({srv_name})", filename)
        self.open_file(filename)

    # --- ГРАФИКА ---
    def _draw_bar_chart(self, data, title, filename):
        plt.style.use('dark_background')

        # Фильтр и сорт
        clean_data = {k: v for k, v in data.items() if v < 900}
        sorted_data = dict(sorted(clean_data.items(), key=lambda x: x[1]))

        names = list(sorted_data.keys())
        values = list(sorted_data.values())
        colors = ['#00ff00' if v < 80 else '#ffff00' if v < 150 else '#ff3333' for v in values]

        plt.figure(figsize=(10, len(names) * 0.5 + 2))
        plt.barh(names, values, color=colors)
        plt.gca().invert_yaxis()
        plt.title(title);
        plt.xlabel("ms")

        for i, v in enumerate(values):
            plt.text(v + 1, i, str(v), va='center', fontsize=8)

        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def _draw_line_chart(self, x, y, title, xlabel, ylabel, filename):
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 6))

        plt.plot(x, y, marker='o', linestyle='-', color='#00ff00', linewidth=2)
        plt.fill_between(x, y, color='#00ff00', alpha=0.1)  # Заливка под графиком

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True, linestyle='--', alpha=0.3)

        plt.savefig(filename)
        plt.close()

    def _draw_dual_line_chart(self, x, y1, y2, title, filename):
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 6))

        plt.plot(x, y1, marker='o', label='Download', color='#00ff00')
        plt.plot(x, y2, marker='o', label='Upload', color='#bd00ff')

        plt.title(title)
        plt.xlabel("Run Number")
        plt.ylabel("Speed (Mbps)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.xticks(x)  # Показывать только целые числа тестов

        plt.savefig(filename)
        plt.close()


# --- МЕНЮ ---
def main_menu():
    app = NetworkMasterPro()

    while True:
        console.clear()
        console.rule("[bold violet]NETWORK DIAGNOSTICS v5.0 (MONITOR EDITION)[/bold violet]")

        rprint("[1] [bold green]Одиночный замер скорости[/bold green] (Classic)")
        rprint("[2] [bold cyan]Мониторинг СКОРОСТИ[/bold cyan] (График стабильности)")
        rprint("[3] [bold yellow]Карта Пингов[/bold yellow] (Весь мир сейчас)")
        rprint("[4] [bold magenta]Мониторинг ПИНГА[/bold magenta] (График 1 сервера во времени)")
        rprint("[0] Выход")

        choice = Prompt.ask("Выбор", choices=["1", "2", "3", "4", "0"], default="3")

        if choice == "0":
            break

        elif choice == "1":
            app.init_speedtest()
            # Для одиночного можно использовать старый метод или просто пропустить
            # Я не стал дублировать код одиночного, так как мониторинг интереснее,
            # но если нужно - можно вызвать run_speed_monitor(iterations=1)
            app.run_speed_monitor()

        elif choice == "2":
            # Тест стабильности
            app.run_speed_monitor()

        elif choice == "3":
            # Общая карта
            app.run_ping_map()

        elif choice == "4":
            # График пинга во времени
            app.run_ping_monitor()

        input("\nНажмите Enter, чтобы продолжить...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExit.")
