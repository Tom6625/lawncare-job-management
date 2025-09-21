() or "MOW"
                name = input("Name: ").strip()
                desc = input("Description (optional): ").strip() or None
                price = input_decimal("Base price: ")
                duration = int(input("Duration minutes: ").strip() or 0)
                svc = create_service(s, code, name, desc, price, duration)
                print(f"Created service [{svc.code}] {svc.name}")
            elif choice == "3":
                sid = int(input("Service ID: ").strip())
                svc = s.get(Service, sid)
                if not svc:
                    print("Service not found")
                    continue
                print("Leave empty to keep current value")
                code = input(f"Code [{svc.code}]: ").strip().upper() or svc.code
                name = input(f"Name [{svc.name}]: ").strip() or svc.name
                desc = input(f"Description [{svc.description or ''}]: ").strip() or svc.description
                price_str = input(f"Base price [{svc.base_price}]: ").strip()
                duration_str = input(f"Duration minutes [{svc.duration_minutes}]: ").strip()
                active_str = input(f"Active (yes/no) [{'yes' if svc.active else 'no'}]: ").strip().lower()
                kwargs = {
                    'code': code,
                    'name': name,
                    'description': desc,
                    'base_price': Decimal(price_str) if price_str else svc.base_price,
                    'duration_minutes': int(duration_str) if duration_str else svc.duration_minutes,
                    'active': (active_str in ['y','yes','1','true']) if active_str else bool(svc.active),
                }
                update_service(s, sid, **kwargs)
                print("Updated.")
            elif choice == "4":
                sid = int(input("Service ID to delete: ").strip())
                ok = delete_service(s, sid)
                print("Deleted" if ok else "Service not found")
            elif choice == "0":
                return
            else:
                print("Invalid option")
        except Exception as e:
            print(f"Error: {e}")

def menu_bookings(s: Session) -> None:
    while True:
        print("\nBookings Menu")
        print("1) List bookings")
        print("2) Add booking")
        print("3) Update booking status/notes/date")
        print("4) Delete booking")
        print("5) Search/filter bookings")
        print("0) Back")
        choice = input("Select: ").strip()
        try:
            if choice == "1":
                print_bookings(s)
            elif choice == "2":
                print_clients(s)
                cid = int(input("Client ID: ").strip())
                print_services(s)
                svc_code = input("Service code: ").strip().upper()
                sdate = input_date("Scheduled date (YYYY-MM-DD): ")
                rep = input("Repeat (none/weekly/fortnightly/monthly): ").strip().lower() or 'none'
                repeat = RepeatFrequency(rep) if rep in RepeatFrequency._value2member_map_ else RepeatFrequency.NONE
                occ = int(input("Occurrences (>=1): ").strip() or 1)
                notes = input("Notes (optional): ").strip() or None
                charge_str = input("Unit charge (blank=use service price): ").strip()
                charge = Decimal(charge_str) if charge_str else None
                b = create_booking(s, cid, svc_code, sdate, repeat, occ, notes, charge)
                print(f"Created booking #{b.id}")
            elif choice == "3":
                bid = int(input("Booking ID: ").strip())
                b = get_booking(s, bid)
                if not b:
                    print("Booking not found")
                    continue
                print("Leave empty to keep current value")
                date_str = input(f"Date [{b.scheduled_date}]: ").strip()
                status_str = input(f"Status ({'/'.join([e.value for e in BookingStatus])}) [{b.status.value}]: ").strip().lower()
                notes = input(f"Notes [{b.notes or ''}]: ").strip()
                kwargs: dict = {}
                if date_str:
                    kwargs['scheduled_date'] = datetime.strptime(date_str, "%Y-%m-%d").date()
                if status_str:
                    kwargs['status'] = BookingStatus(status_str)
                if notes:
                    kwargs['notes'] = notes
                update_booking(s, bid, **kwargs)
                print("Updated.")
            elif choice == "4":
                bid = int(input("Booking ID to delete: ").strip())
                ok = delete_booking(s, bid)
                print("Deleted" if ok else "Booking not found")
            elif choice == "5":
                client_filter = input("Client ID (blank=any): ").strip()
                cid = int(client_filter) if client_filter else None
                status_str = input(f"Status filter ({'/'.join([e.value for e in BookingStatus])}|blank=any): ").strip().lower()
                status = BookingStatus(status_str) if status_str in BookingStatus._value2member_map_ else None
                sd = input("Start date (YYYY-MM-DD or blank): ").strip()
                ed = input("End date (YYYY-MM-DD or blank): ").strip()
                start = datetime.strptime(sd, "%Y-%m-%d").date() if sd else None
                end = datetime.strptime(ed, "%Y-%m-%d").date() if ed else None
                results = list_bookings(s, client_id=cid, status=status, start_date=start, end_date=end)
                print_bookings(s, results)
            elif choice == "0":
                return
            else:
                print("Invalid option")
        except Exception as e:
            print(f"Error: {e}")


# =====
# Main
# =====

def seed_defaults(s: Session) -> None:
    if not list_services(s):
        create_service(s, "MOW", "Mowing", "Standard lawn mowing", Decimal("60.00"), 45)
        create_service(s, "EDGE", "Edging", "Edge trimming around paths and beds", Decimal("35.00"), 30)
        create_service(s, "TRIM", "Trimming", "Hedge/bush trimming", Decimal("80.00"), 60)


def interactive_menu() -> None:
    init_db()
    with SessionLocal() as s:
        seed_defaults(s)
        while True:
            print("\nLawncare Management - Main Menu")
            print("1) Clients")
            print("2) Services")
            print("3) Bookings")
            print("0) Exit")
            ch = input("Select: ").strip()
            if ch == "1":
                menu_clients(s)
            elif ch == "2":
                menu_services(s)
            elif ch == "3":
                menu_bookings(s)
            elif ch == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option")


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Application entrypoint.

    Args:
        argv: Optional iterable of CLI args (for testing).

    Returns:
        int: Process exit code (0=success).

    Notes:
        This CLI-centric structure keeps business logic (models & repository
        functions) separate from presentation, easing future migration to a
        Flask/FastAPI API. You can import models and repository functions in a
        web project and reuse them directly.
    """
    parser = argparse.ArgumentParser(description="Lawncare Job Management CLI")
    parser.add_argument("--non-interactive", action="store_true", help="Run a short demo and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    init_db()
    with SessionLocal() as s:
        seed_defaults(s)
        if args.non_interactive:
            # demo: add a client and a repeat booking, then list
            c = create_client(s, "Jane", "Doe", "jane@example.com", "+1-555-1111", "12 Green St", "Gate code 1234")
            create_booking(s, c.id, "MOW", date.today(), repeat=RepeatFrequency.FORTNIGHTLY, occurrences=3, notes="Front and back")
            print("\n-- Clients --")
            print_clients(s)
            print("\n-- Services --")
            print_services(s)
            print("\n-- Bookings --")
            print_bookings(s)
            return 0
        else:
            interactive_menu()
            return 0


if __name__ == "__main__":
    sys.exit(main())
