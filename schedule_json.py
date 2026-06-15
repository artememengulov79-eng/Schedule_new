import calendar
import csv
import random
import json
import os

# ================= КОНФИГУРАЦИЯ ГРАФИКА (БЕЗ ИЗМЕНЕНИЙ) =================

def generate_schedule(employees, year, month, shift_config, absences, shuffle_iterations=1000):
    """
    Вариант 3: Двухэтапный алгоритм.
    Учитывает: Допуски, Отдых, ОТСУТСТВИЯ.
    """
    _, num_days = calendar.monthrange(year, month)
    
    # --- ЭТАП 1: Создание сбалансированного скелета ---
    schedule = {}
    emp_shifts_count = {emp: 0 for emp in employees}

    for day in range(1, num_days + 1):
        needed_shifts = []
        for shift_type, config in shift_config.items():
            if config["daily"] or day in config["dates"]:
                needed_shifts.append(shift_type)
        
        for s_type in needed_shifts:
            allowed = shift_config[s_type]["allowed_employees"]
            
            # 🟢 ФИЛЬТР: Допущенные + НЕ ОТСУТСТВУЮЩИЕ
            candidates = [
                emp for emp in employees 
                if emp in allowed and day not in absences.get(emp, [])
            ]
            
            candidates.sort(key=lambda e: emp_shifts_count[e])
            
            chosen = None
            for emp in candidates:
                if _is_valid_placement(emp, day, s_type, schedule, shift_config, num_days):
                    chosen = emp
                    break
            
            if chosen:
                schedule[(chosen, day)] = s_type
                emp_shifts_count[chosen] += 1

    # --- ЭТАП 2: Рандомизация (Перемешивание) ---
    current_shifts = []
    for (emp, day), s_type in schedule.items():
        current_shifts.append({'day': day, 'type': s_type, 'emp': emp})
        
    for _ in range(shuffle_iterations):
        if len(current_shifts) < 2: break
        
        s1 = random.choice(current_shifts)
        s2 = random.choice(current_shifts)
        
        if s1['type'] != s2['type'] or s1['emp'] == s2['emp']:
            continue
            
        emp1, day1 = s1['emp'], s1['day']
        emp2, day2 = s2['emp'], s2['day']
        s_type = s1['type']
        
        allowed = shift_config[s_type]["allowed_employees"]
        if emp1 not in allowed or emp2 not in allowed: continue
        
        if day2 in absences.get(emp1, []): continue
        if day1 in absences.get(emp2, []): continue
            
        if _can_take_shift(emp1, day2, s_type, current_shifts, shift_config) and \
           _can_take_shift(emp2, day1, s_type, current_shifts, shift_config):
            s1['emp'] = emp2
            s2['emp'] = emp1

    final_schedule = {}
    for s in current_shifts:
        final_schedule[(s['emp'], s['day'])] = s['type']

    return final_schedule, num_days

def _is_valid_placement(emp, day, shift_type, schedule, shift_config, num_days):
    rest_days = shift_config[shift_type]["rest_days"]
    for (e, d), t in schedule.items():
        if e == emp:
            other_rest = shift_config[t]["rest_days"]
            if d == day: return False
            if d > day:
                if d < day + rest_days + 1: return False
            else:
                if day < d + other_rest + 1: return False
    return True

def _can_take_shift(emp, target_day, target_type, shifts_list, shift_config):
    target_rest = shift_config[target_type]["rest_days"]
    for s in shifts_list:
        if s['emp'] == emp:
            if s['day'] != target_day:
                other_rest = shift_config[s['type']]["rest_days"]
                if s['day'] > target_day:
                    if s['day'] < target_day + target_rest + 1: return False
                else:
                    if target_day < s['day'] + other_rest + 1: return False
    return True

def print_matrix_schedule(schedule, employees, num_days, absences):
    """Выводит график с пометкой '*' в дни отсутствия."""
    header = f"{'ФИО':<16}|"
    for d in range(1, num_days + 1):
        header += f" {d:02d} |"
    print(header)
    print("-" * len(header))

    for emp in employees:
        row = f"{emp:<16}|"
        emp_absent_days = absences.get(emp, [])
        
        for d in range(1, num_days + 1):
            if d in emp_absent_days:
                val = "*"
            else:
                val = schedule.get((emp, d), "")
            row += f" {str(val):^3}|"
        print(row)

def export_to_csv(schedule, employees, year, month, num_days, absences, filename="график_дежурств.json_данные.csv"):
    """Экспортирует график в CSV с пометкой '*' в дни отсутствия."""
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ФИО"] + [f"{d:02d}.{month:02d}" for d in range(1, num_days + 1)])
        for emp in employees:
            row = [emp]
            emp_absent_days = absences.get(emp, [])
            for d in range(1, num_days + 1):
                if d in emp_absent_days:
                    row.append("*")
                else:
                    row.append(schedule.get((emp, d), ""))
            writer.writerow(row)
    print(f"\n✅ Файл '{filename}' создан.")


# ================= ЗАГРУЗКА ДАННЫХ ИЗ JSON =================

def load_json_file(filename):
    """Загружает данные из JSON файла."""
    if not os.path.exists(filename):
        print(f"⚠️ Файл '{filename}' не найден. Будет создан пустой шаблон.")
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f" Ошибка чтения JSON в файле '{filename}'. Проверьте формат.")
        return {}

if __name__ == "__main__":
    #  НАСТРОЙКИ ПЕРИОДА
    YEAR, MONTH = 2026, 6
    month_key = f"{YEAR}-{MONTH:02d}"

    print(f"📅 Планирование графика на {calendar.month_name[MONTH]} {YEAR}")
    print("Загрузка данных из JSON файлов...")

    # 1. ЗАГРУЗКА СОТРУДНИКОВ
    # Файл должен содержать список: ["Иванов", "Петров"]
    raw_employees = load_json_file("employees.json")
    if isinstance(raw_employees, list):
        EMPLOYEES = raw_employees
    else:
        EMPLOYEES = []
        print("⚠️ В employees.json должен быть список имен.")

    print(f"👥 Загружено сотрудников: {len(EMPLOYEES)}")

    # 2. ЗАГРУЗКА ВИДОВ ДЕЖУРСТВ (с поддержкой месяцев)
    raw_shifts_all = load_json_file("shifts.json")
    
    # Ищем правила для текущего месяца, если нет -> берём "default", если нет -> пусто
    month_shifts_raw = raw_shifts_all.get(month_key, raw_shifts_all.get("default", {}))
    
    shift_config = {}
    for s_name, s_data in month_shifts_raw.items():
        dates = [int(d) for d in s_data.get("dates", [])]
        rest = int(s_data.get("rest_days", 1))
        allowed = s_data.get("allowed_employees", [])
        
        # Фильтруем допущенных: оставляем только тех, кто есть в актуальном списке
        valid_allowed = [emp for emp in allowed if emp in EMPLOYEES]
        
        shift_config[s_name] = {
            "daily": s_data.get("daily", False),
            "dates": dates,
            "rest_days": rest,
            "allowed_employees": valid_allowed
        }
        print(f"   📌 Вид '{s_name}': допущено {len(valid_allowed)} чел.")

    # 3. ЗАГРУЗКА ОТСУТСТВИЙ
    # Файл содержит словарь { "2026-06": { "Иванов": [1,2] }, ... }
    raw_absences_all = load_json_file("absences.json")
    # Берем данные только для текущего месяца
    ABSENCES = raw_absences_all.get(month_key, {})
    
    abs_count = sum(len(d) for d in ABSENCES.values())
    print(f"   🏖️ Отсутствий в этом месяце: {abs_count} дн.")

    # ПРОВЕРКА ДАННЫХ
    if not EMPLOYEES:
        print(" Список сотрудников пуст. Создайте файл employees.json")
        exit()
    if not shift_config:
        print("❌ Настройки смен пусты. Создайте файл shifts.json")
        exit()

    # 🚀 ГЕНЕРАЦИЯ
    print("\n🔄 Генерация графика...")
    schedule, num_days = generate_schedule(EMPLOYEES, YEAR, MONTH, shift_config, ABSENCES, shuffle_iterations=1000)
    
    #  ВЫВОД
    print("\n")
    print_matrix_schedule(schedule, EMPLOYEES, num_days, ABSENCES)
    export_to_csv(schedule, EMPLOYEES, YEAR, MONTH, num_days, ABSENCES)

    #  СТАТИСТИКА
    print("\n Распределение смен:")
    for emp in EMPLOYEES:
        counts = {t: 0 for t in shift_config}
        for d in range(1, num_days + 1):
            val = schedule.get((emp, d))
            if val in counts:
                counts[val] += 1
        total = sum(counts.values())
        absent_days = len(ABSENCES.get(emp, []))
        print(f"  {emp}: {counts} (всего: {total}) | Отсутствует: {absent_days} дн.")