"""
Seed fake data for development/testing: creates/updates two teams (intlum, logic)
and at least 10 rows per other table (memberapp + hardwareapp).
Users and hardware are scoped to those team names only (other teams in DB are ignored).
Run: python manage.py seed_fake_data
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from memberapp.models import Team, Department, Designation
from hardwareapp.models import (
    OperatingSystemTable,
    ProcessorTable,
    GraphicsCardTable,
    MotherboardTable,
    RAMTable,
    HDDTable,
    SSDTable,
    LiquidCoolerTable,
    UPSTable,
    MonitorTable,
    KeyboardTable,
    MouseTable,
    HeadphoneTable,
    Pentable,
    SpeakerTable,
    WebcamTable,
    PowerSupplyTable,
    CabinetTable,
    MachineTable,
    MachineProcessorThrough,
    MachineRAMThrough,
    MachineSSDThrough,
    MachineMotherboardThrough,
    MachinePowerSupplyThrough,
    MachineCabinetThrough,
    MachineLiquidCoolerThrough,
)

# Only these two teams are created for team table.
TEAM_SEED = [
    {"name": "intlum", "code": "INTLUM", "description": "Intlum team (testing)."},
    {"name": "logic", "code": "LOGIC", "description": "Logic team (testing)."},
]

COUNT = 10


def make_fake_department(i):
    names = [
        "Backend", "Frontend", "DevOps", "QA", "HR",
        "Data", "Security", "Mobile", "Support", "Sales",
    ]
    codes = ["BE", "FE", "DO", "QA", "HR", "DATA", "SEC", "MOB", "SUP", "SLS"]
    return {"name": names[i], "code": codes[i], "description": f"Department {names[i]}."}


def make_fake_designation(i):
    names = [
        "Developer", "Lead", "Manager", "Analyst", "Intern",
        "Architect", "Designer", "Engineer", "Director", "Specialist",
    ]
    codes = ["DEV", "LEAD", "MGR", "ANA", "INT", "ARC", "DSN", "ENG", "DIR", "SPC"]
    return {"name": names[i], "code": codes[i], "description": f"Role: {names[i]}."}


def make_fake_os(i):
    names = [
        "Ubuntu", "Windows", "macOS", "CentOS", "Debian",
        "Fedora", "Rocky Linux", "AlmaLinux", "openSUSE", "Arch Linux",
    ]
    versions = ["22.04", "11", "14", "8", "12", "40", "9.3", "9.4", "15.5", "rolling"]
    return {"name": names[i], "version": versions[i]}


def make_fake_processor(i):
    brands = [
        "Intel", "AMD", "Apple", "Qualcomm", "ARM",
        "IBM", "NVIDIA", "Samsung", "HiSilicon", "Broadcom",
    ]
    models = [
        "Core i7", "Ryzen 9", "M2", "Snapdragon", "Cortex-A78",
        "POWER10", "Grace", "Exynos", "Kirin", "Vulcan",
    ]
    return {
        "name": f"{brands[i]} {models[i]}",
        "brand": brands[i],
        "model": models[i],
        "architecture": random.choice(["x86_64", "ARM64", "x86"]),
        "cores": random.randint(4, 16),
        "threads": random.randint(8, 32),
        "frequency": f"{random.randint(2, 5)}.{random.randint(0, 9)} GHz",
        "cache": f"{random.choice([8, 12, 16, 24, 32])} MB",
        "quantity": random.randint(5, 50),
    }


def make_fake_generic_hardware(i, brands, model_suffix="Pro"):
    b = brands[i % len(brands)]
    return {
        "name": f"{b} {model_suffix} {i+1}",
        "brand": b,
        "model": f"{model_suffix}-{1000 + i}",
        "quantity": random.randint(5, 30),
    }


def make_fake_graphics(i):
    brands = [
        "NVIDIA", "AMD", "Intel", "ASUS", "MSI",
        "Gigabyte", "Zotac", "EVGA", "PNY", "Palit",
    ]
    return {
        **make_fake_generic_hardware(i, brands, "RTX"),
        "memory": random.choice([4, 6, 8, 12, 16]) * 1024,
    }


def make_fake_motherboard(i):
    brands = [
        "ASUS", "MSI", "Gigabyte", "ASRock", "EVGA",
        "Biostar", "Supermicro", "NZXT", "Razer", "TUF",
    ]
    base = make_fake_generic_hardware(i, brands, "B550")
    base["socket"] = random.choice(["AM5", "LGA1700", "AM4", "LGA1200", "sTRX4"])
    base["memory_slots"] = random.choice([2, 4, 8])
    return base


def make_fake_ram(i):
    brands = [
        "Corsair", "G.Skill", "Kingston", "Crucial", "Samsung",
        "ADATA", "TeamGroup", "Patriot", "HyperX", "Lexar",
    ]
    base = make_fake_generic_hardware(i, brands, "DDR4")
    base["memory"] = random.choice([8, 16, 32, 64]) * 1024
    return base


def make_fake_storage(i, model_class):
    brands = [
        "Samsung", "WD", "Seagate", "Crucial", "Kingston",
        "Toshiba", "Hitachi", "Intel", "ADATA", "SanDisk",
    ]
    suffix = "EVO" if "SSD" in model_class else "Barracuda"
    base = make_fake_generic_hardware(i, brands, suffix)
    base["capacity"] = random.choice([256, 512, 1000, 2000, 4000])
    return base


def make_fake_liquid_cooler(i):
    brands = [
        "Corsair", "NZXT", "Cooler Master", "Arctic", "Noctua",
        "be quiet!", "Lian Li", "Deepcool", "Thermaltake", "Fractal",
    ]
    base = make_fake_generic_hardware(i, brands, "AIO")
    base["is_liquid"] = random.choice([True, False])
    return base


def make_fake_ups(i):
    brands = [
        "APC", "Eaton", "CyberPower", "Tripp Lite", "Vertiv",
        "Schneider", "Delta", "Emerson", "Legrand", "Socomec",
    ]
    return make_fake_generic_hardware(i, brands, "Smart")


def make_fake_monitor(i):
    brands = [
        "Dell", "LG", "Samsung", "ASUS", "BenQ",
        "Acer", "HP", "Lenovo", "ViewSonic", "AOC",
    ]
    return make_fake_generic_hardware(i, brands, "UltraSharp")


def make_fake_keyboard(i):
    brands = [
        "Logitech", "Keychron", "Corsair", "Razer", "Microsoft",
        "SteelSeries", "Ducky", "HyperX", "Filco", "Varmilo",
    ]
    return make_fake_generic_hardware(i, brands, "K")


def make_fake_mouse(i):
    brands = [
        "Logitech", "Razer", "Microsoft", "SteelSeries", "HP",
        "Corsair", "Zowie", "Roccat", "Glorious", "Pulsar",
    ]
    return make_fake_generic_hardware(i, brands, "MX")


def make_fake_headphone(i):
    brands = [
        "Sony", "Bose", "Sennheiser", "Jabra", "Logitech",
        "Audio-Technica", "Beyerdynamic", "HyperX", "SteelSeries", "Apple",
    ]
    return make_fake_generic_hardware(i, brands, "WH")


def make_fake_pentable(i):
    brands = [
        "IKEA", "FlexiSpot", "Fully", "Uplift", "Autonomous",
        "Vari", "Jarvis", "Herman Miller", "Steelcase", "Humanscale",
    ]
    return make_fake_generic_hardware(i, brands, "Standing")


def make_fake_speaker(i):
    brands = [
        "Logitech", "Creative", "Bose", "JBL", "Edifier",
        "Klipsch", "Audioengine", "Sonos", "Marshall", "Harman Kardon",
    ]
    return make_fake_generic_hardware(i, brands, "Z")


def make_fake_webcam(i):
    brands = [
        "Logitech", "Razer", "Microsoft", "HP", "Elgato",
        "Anker", "Ausdom", "Lenovo", "Dell", "Poly",
    ]
    return make_fake_generic_hardware(i, brands, "C920")


def make_fake_power_supply(i):
    brands = [
        "Corsair", "Seasonic", "EVGA", "be quiet!", "Cooler Master",
        "Thermaltake", "Antec", "FSP", "Silverstone", "Fractal",
    ]
    return make_fake_generic_hardware(i, brands, "RMx")


def make_fake_cabinet(i):
    brands = [
        "NZXT", "Fractal", "Corsair", "Lian Li", "Cooler Master",
        "Phanteks", "be quiet!", "Thermaltake", "Silverstone", "Antec",
    ]
    return make_fake_generic_hardware(i, brands, "H510")


class Command(BaseCommand):
    help = "Seed fake data: 2 teams (intlum, logic), 10+ rows per other table (memberapp + hardwareapp)."

    def handle(self, *args, **options):
        User = get_user_model()

        # ----- Member app -----
        self.stdout.write("Seeding memberapp (2 teams, 10 departments/designations, 10 users)...")
        for spec in TEAM_SEED:
            Team.objects.get_or_create(name=spec["name"], defaults=spec)

        for i in range(COUNT):
            Department.objects.get_or_create(
                name=make_fake_department(i)["name"],
                defaults=make_fake_department(i),
            )
            Designation.objects.get_or_create(
                name=make_fake_designation(i)["name"],
                defaults=make_fake_designation(i),
            )

        team_names = [s["name"] for s in TEAM_SEED]
        teams = list(
            Team.objects.filter(is_delete=False, name__in=team_names).order_by("name")
        )
        # Expect intlum then logic when ordered by name
        departments = list(Department.objects.filter(is_delete=False).order_by("pk")[:COUNT])
        designations = list(Designation.objects.filter(is_delete=False).order_by("pk")[:COUNT])

        for i in range(COUNT):
            username = f"user{i+1}"
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f"user{i+1}@example.com",
                    password="seedpass123",
                    first_name=f"First{i+1}",
                    last_name=f"Last{i+1}",
                    employee_id=f"EMP{i+1:04d}",
                    phone=f"+1555000{i}{i}{i}{i}",
                    team=teams[i % len(teams)] if teams else None,
                    department=departments[i] if i < len(departments) else None,
                    designation=designations[i] if i < len(designations) else None,
                )

        if len(teams) < 2:
            self.stdout.write(self.style.WARNING("Expected 2 teams (intlum, logic); check Team table."))

        # ----- Hardware app (components are per-team; alternate teams for 10 rows total) -----
        if not teams:
            self.stdout.write(self.style.WARNING("No team found; skipping hardware seed."))
            self.stdout.write(self.style.SUCCESS("Done. Member data only."))
            return

        self.stdout.write("Seeding hardwareapp (operating_system)...")
        for i in range(COUNT):
            data = make_fake_os(i)
            OperatingSystemTable.objects.get_or_create(
                name=data["name"], version=data["version"], defaults=data
            )

        def team_for_row(i):
            return teams[i % len(teams)]

        # ----- Hardware app: processors -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_processor(i), "team_id": t.pk}
            name = data["name"]
            if not ProcessorTable.objects.filter(name=name, team_id=t.pk).exists():
                ProcessorTable.objects.create(**data)

        # ----- Hardware app: graphics cards -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_graphics(i), "team_id": t.pk}
            name = data["name"]
            if not GraphicsCardTable.objects.filter(name=name, team_id=t.pk).exists():
                GraphicsCardTable.objects.create(**data)

        # ----- Hardware app: motherboards -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_motherboard(i), "team_id": t.pk}
            name = data["name"]
            if not MotherboardTable.objects.filter(name=name, team_id=t.pk).exists():
                MotherboardTable.objects.create(**data)

        # ----- Hardware app: RAM -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_ram(i), "team_id": t.pk}
            name = data["name"]
            if not RAMTable.objects.filter(name=name, team_id=t.pk).exists():
                RAMTable.objects.create(**data)

        # ----- Hardware app: HDD / SSD -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_storage(i, "HDD"), "team_id": t.pk}
            name = data["name"]
            if not HDDTable.objects.filter(name=name, team_id=t.pk).exists():
                HDDTable.objects.create(**data)
            data = {**make_fake_storage(i, "SSD"), "team_id": t.pk}
            name = data["name"]
            if not SSDTable.objects.filter(name=name, team_id=t.pk).exists():
                SSDTable.objects.create(**data)

        # ----- Hardware app: liquid cooler -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_liquid_cooler(i), "team_id": t.pk}
            name = data["name"]
            if not LiquidCoolerTable.objects.filter(name=name, team_id=t.pk).exists():
                LiquidCoolerTable.objects.create(**data)

        # ----- Hardware app: UPS -----
        for i in range(COUNT):
            t = team_for_row(i)
            data = {**make_fake_ups(i), "team_id": t.pk}
            name = data["name"]
            if not UPSTable.objects.filter(name=name, team_id=t.pk).exists():
                UPSTable.objects.create(**data)

        # ----- Hardware app: peripherals -----
        peripherals = [
            (MonitorTable, make_fake_monitor),
            (KeyboardTable, make_fake_keyboard),
            (MouseTable, make_fake_mouse),
            (HeadphoneTable, make_fake_headphone),
            (Pentable, make_fake_pentable),
            (SpeakerTable, make_fake_speaker),
            (WebcamTable, make_fake_webcam),
            (PowerSupplyTable, make_fake_power_supply),
            (CabinetTable, make_fake_cabinet),
        ]
        for model_class, maker in peripherals:
            self.stdout.write(f"Seeding {model_class.__name__}...")
            for i in range(COUNT):
                t = team_for_row(i)
                data = {**maker(i), "team_id": t.pk}
                name = data["name"]
                if not model_class.objects.filter(name=name, team_id=t.pk).exists():
                    model_class.objects.create(**data)

        # ----- Hardware app: machines (5 per team = 10 total) -----
        self.stdout.write("Seeding hardwareapp (machines)...")
        os_list = list(OperatingSystemTable.objects.filter(is_delete=False).order_by("pk")[:COUNT])

        for team in teams:
            users = list(User.objects.filter(team=team).order_by("pk"))
            procs = list(ProcessorTable.objects.filter(team=team).order_by("pk"))
            rams = list(RAMTable.objects.filter(team=team).order_by("pk"))
            ssds = list(SSDTable.objects.filter(team=team).order_by("pk"))
            mobos = list(MotherboardTable.objects.filter(team=team).order_by("pk"))
            psus = list(PowerSupplyTable.objects.filter(team=team).order_by("pk"))
            cabinets = list(CabinetTable.objects.filter(team=team).order_by("pk"))
            coolers = list(LiquidCoolerTable.objects.filter(team=team).order_by("pk"))

            if not (os_list and procs and rams and ssds and mobos and psus and cabinets and coolers):
                self.stdout.write(
                    self.style.WARNING(f"Missing required components for team {team.name}; skipping machines for this team.")
                )
                continue

            for mi in range(5):
                code = team.code or team.name.upper()
                name = f"WS-{code}-{mi+1:02d}"
                if MachineTable.objects.filter(name=name, team=team).exists():
                    continue
                u = users[mi] if mi < len(users) else None
                dept = u.department if u and u.department_id else departments[0]
                machine = MachineTable.objects.create(
                    name=name,
                    code=f"{code}-{1000 + mi}",
                    description=f"Seeded machine {mi+1} ({team.name}).",
                    team=team,
                    member=u,
                    department=dept,
                )
                machine.operating_system.add(os_list[mi % len(os_list)])
                MachineProcessorThrough.objects.create(
                    machine=machine, processor=procs[mi % len(procs)], quantity=1
                )
                MachineRAMThrough.objects.create(machine=machine, ram=rams[mi % len(rams)], quantity=1)
                MachineSSDThrough.objects.create(machine=machine, ssd=ssds[mi % len(ssds)], quantity=1)
                MachineMotherboardThrough.objects.create(
                    machine=machine, motherboard=mobos[mi % len(mobos)], quantity=1
                )
                MachinePowerSupplyThrough.objects.create(
                    machine=machine, power_supply=psus[mi % len(psus)], quantity=1
                )
                MachineCabinetThrough.objects.create(
                    machine=machine, cabinet=cabinets[mi % len(cabinets)], quantity=1
                )
                MachineLiquidCoolerThrough.objects.create(
                    machine=machine, liquid_cooler=coolers[mi % len(coolers)], quantity=1
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Done. Teams: intlum + logic; 10 rows per other table (5 machines per team = 10 machines)."
            )
        )
