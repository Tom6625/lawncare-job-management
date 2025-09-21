"""
Lawncare Job Management - CLI Prototype (app.py)

This module provides a simple command-line prototype for managing:
- Clients (stored in an in-memory client database)
- Services (a catalog/list of offered services)
- Jobs/Bookings (including support for repeat bookings)

It includes basic add/list functionality for each domain and is structured with
future web integration in mind (FastAPI/Flask/Django placeholders provided).

Usage (CLI):
  python app.py            # interactive menu
  python app.py --help     # see arguments

Note: This is a prototype. Data is stored in-memory and will be lost on exit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Iterable
import argparse
import itertools
import sys

# ==========================
# Domain Models
# ==========================

@dataclass
class Client:
    """Represents a client/customer for lawncare services.

    Fields:
        id: Unique identifier for the client (int).
        first_name: Client first name.
        last_name: Client last name.
        email: Contact email address.
        phone: Contact phone number.
        address: Service address (street, city, postcode).
        notes: Freeform notes (gate code, pets, etc.).
    """

    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    notes: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class Service:
    """Represents a billable service offered by the business.

    Fields:
        code: Short unique code for the service (e.g., MOW, EDGE).
        name: Human-readable service name.
        description: What is included.
        base_price: Base price in local currency (float prototype; consider Decimal in prod).
        duration_minutes: Typical duration in minutes.
    """

    code: str
    name: str
    description: str
    base_price: float
    duration_minutes: int


class RepeatFrequency(Enum):
    NONE = "none"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"


@dataclass
class Booking:
    """Represents a scheduled job/booking for a client.

    Fields:
        id: Unique booking id.
        client_id: ID of the client.
        service_code: Code of the service to perform.
        scheduled_date: The first scheduled date of the job.
        repeat: Repeat frequency (none/weekly/fortnightly/monthly).
        occurrences: Number of repeats including the first one (1 = one-off).
        notes: Optional notes.
    """

    id: int
    client_id: int
    service_code: str
    scheduled_date: date
    repeat: RepeatFrequency = RepeatFrequency.NONE
    occurrences: int = 1
    notes: str = ""

    def occurrence_dates(self) -> List[date]:
        """Compute all occurrence dates for the booking, based on repeat pattern."""
        if self.occurrences <= 1 or self.repeat == RepeatFrequency.NONE:
            return [self.scheduled_date]

        dates: List[date] = [self.scheduled_date]
        current = self.scheduled_date
        for _ in range(self.occurrences - 1):
            if self.repeat == RepeatFrequency.WEEKLY:
                current = current + timedelta(weeks=1)
            elif self.repeat == RepeatFrequency.FORTNIGHTLY:
                current = current + timedelta(weeks=2)
            elif self.repeat == RepeatFrequency.MONTHLY:
                # Simple month add prototype: add ~30 days; in production use dateutil.relativedelta
                current = current + timedelta(days=30)
            dates.append(current)
        return dates


# ==========================
# In-Memory Stores
# ==========================

class ClientDB:
    """A simple in-memory client database with add/get/list operations.

    In production, replace with a repository/DAO backed by a real database
    (e.g., PostgreSQL via SQLAlchemy). Methods are designed to keep parity
    with future persistence implementations.
    """

    def __init__(self) -> None:
        self._clients: Dict[int, Client] = {}
        self._id_counter = itertools.count(1)

    def add(self, first_name: str, last_name: str, email: str, phone: str, address: str, notes: str = "") -> Client:
        cid = next(self._id_counter)
        client = Client(
            id=cid,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            notes=notes,
        )
        self._clients[cid] = client
        return client

    def get(self, client_id: int) -> Optional[Client]:
        return self._clients.get(client_id)

    def list(self) -> List[Client]:
        return list(self._clients.values())


class ServiceCatalog:
    """A simple catalog for available services with add/list operations.

    Consider loading defaults from a JSON/YAML file or database in the future.
    """

    def __init__(self) -> None:
        self._services: Dict[str, Service] = {}

    def add(self, code: str, name: str, description: str, base_price: float, duration_minutes: int) -> Service:
        svc = Service(code=code.upper(), name=name, description=description, base_price=base_price, duration_minutes=duration_minutes)
        self._services[svc.code] = svc
        return svc

    def get(self, code: str) -> Optional[Service]:
        return self._services.get(code.upper())

    def list(self) -> List[Service]:
        return list(self._services.values())


class BookingManager:
    """Manage bookings, including repeat scheduling."""

    def __init__(self) -> None:
        self._bookings: Dict[int, Booking] = {}
        self._id_counter = itertools.count(1)

    def add(
        self,
        client_id: int,
        service_code: str,
        scheduled_date: date,
        repeat: RepeatFrequency = RepeatFrequency.NONE,
        occurrences: int = 1,
        notes: str = "",
    ) -> Booking:
        bid = next(self._id_counter)
        booking = Booking(
            id=bid,
            client_id=client_id,
            service_code=service_code.upper(),
            scheduled_date=scheduled_date,
            repeat=repeat,
            occurrences=max(1, occurrences),
            notes=notes,
        )
        self._bookings[bid] = booking
        return booking

    def get(self, booking_id: int) -> Optional[Booking]:
        return self._bookings.get(booking_id)

    def list(self) -> List[Booking]:
        return list(self._bookings.values())


# ==========================
# CLI Interface
# ==========================

def _seed_data(clients: ClientDB, services: ServiceCatalog) -> None:
    """Seed some demo data for quick testing in the CLI prototype."""
    if not clients.list():
        clients.add("Jane", "Doe", "jane@example.com", "+1-555-1111", "12 Green St, Springfield 12345")
        clients.add("John", "Smith", "john@example.com", "+1-555-2222", "34 Oak Ave, Shelbyville 67890", notes="Has large dog in backyard")
    if not services.list():
        services.add("MOW", "Mowing", "Standard lawn mowing", 60.0, 45)
        services.add("EDGE", "Edging", "Edge trimming around paths and beds", 35.0, 30)
        services.add("TRIM", "Trimming", "Hedge/bush trimming", 80.0, 60)


def _print_clients(clients: ClientDB) -> None:
    print("\nClients:")
    for c in clients.list():
        print(f"  [{c.id}] {c.full_name} | {c.email} | {c.phone} | {c.address}")


def _print_services(services: ServiceCatalog) -> None:
    print("\nServices:")
    for s in services.list():
        print(f"  [{s.code}] {s.name} - ${s.base_price:.2f} for ~{s.duration_minutes} min")


def _print_bookings(bookings: BookingManager, clients: ClientDB, services: ServiceCatalog) -> None:
    print("\nBookings:")
    for b in bookings.list():
        client = clients.get(b.client_id)
        svc = services.get(b.service_code)
        svc_name = svc.name if svc else b.service_code
        occ = ", ".join(d.isoformat() for d in b.occurrence_dates())
        print(
            f"  [#{b.id}] {client.full_name if client else 'Unknown Client'} - {svc_name} on {b.scheduled_date.isoformat()} "
            f"(repeat={b.repeat.value}, occurrences={b.occurrences})\n      -> Occurrences: {occ}"
        )


def interactive_menu() -> None:
    """Simple interactive CLI loop for adding/listing entities."""
    clients = ClientDB()
    services = ServiceCatalog()
    bookings = BookingManager()
    _seed_data(clients, services)

    while True:
        print("\nLawncare Job Management - Menu")
        print("1) List clients")
        print("2) Add client")
        print("3) List services")
        print("4) Add service")
        print("5) List bookings")
        print("6) Add booking")
        print("0) Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                _print_clients(clients)
            elif choice == "2":
                first = input("First name: ").strip()
                last = input("Last name: ").strip()
                email = input("Email: ").strip()
                phone = input("Phone: ").strip()
                address = input("Address: ").strip()
                notes = input("Notes (optional): ").strip()
                client = clients.add(first, last, email, phone, address, notes)
                print(f"Added client #{client.id}: {client.full_name}")
            elif choice == "3":
                _print_services(services)
            elif choice == "4":
                code = input("Service code (e.g., MOW): ").strip()
                name = input("Name: ").strip()
                description = input("Description: ").strip()
                price = float(input("Base price: ").strip() or 0)
                duration = int(input("Duration (minutes): ").strip() or 0)
                svc = services.add(code, name, description, price, duration)
                print(f"Added service [{svc.code}] {svc.name}")
            elif choice == "5":
                _print_bookings(bookings, clients, services)
            elif choice == "6":
                _print_clients(clients)
                client_id = int(input("Client ID: ").strip())
                _print_services(services)
                service_code = input("Service code: ").strip()
                date_str = input("Scheduled date (YYYY-MM-DD): ").strip()
                scheduled_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                repeat_str = input("Repeat (none/weekly/fortnightly/monthly): ").strip().lower() or "none"
                repeat = RepeatFrequency(repeat_str) if repeat_str in RepeatFrequency._value2member_map_ else RepeatFrequency.NONE
                occurrences = int(input("Occurrences (>=1): ").strip() or 1)
                notes = input("Notes (optional): ").strip()
                booking = bookings.add(
                    client_id=client_id,
                    service_code=service_code,
                    scheduled_date=scheduled_date,
                    repeat=repeat,
                    occurrences=occurrences,
                    notes=notes,
                )
                print(f"Added booking #{booking.id} for client {client_id} on {scheduled_date.isoformat()}")
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"Error: {e}")


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry point for CLI usage via argparse and interactive menu.

    In the future, this function may dispatch to:
      - FastAPI app (uvicorn) for an API-first design
      - Flask/Django routes for web interface
      - Celery/RQ workers for background scheduling/billing
    """
    parser = argparse.ArgumentParser(description="Lawncare Job Management CLI (prototype)")
    parser.add_argument("--non-interactive", action="store_true", help="Run a brief demo and exit (non-interactive)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Initialize stores
    clients = ClientDB()
    services = ServiceCatalog()
    bookings = BookingManager()
    _seed_data(clients, services)

    if args.non_interactive:
        # Demonstration run: list seed data and create a sample repeat booking
        print("Demo mode: listing seed data and creating a sample booking...\n")
        _print_clients(clients)
        _print_services(services)
        sample = bookings.add(
            client_id=1,
            service_code="MOW",
            scheduled_date=date.today(),
            repeat=RepeatFrequency.FORTNIGHTLY,
            occurrences=3,
            notes="Front and back lawns",
        )
        _print_bookings(bookings, clients, services)
        print("\nDone.")
        return 0

    # Interactive menu
    interactive_menu()
    return 0


if __name__ == "__main__":
    sys.exit(main())
