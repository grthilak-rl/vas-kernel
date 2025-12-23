#!/usr/bin/env python3
"""
CLI tool for managing API keys.

Usage:
    python scripts/manage_api_keys.py create --name "Ruth-AI" --description "API key for Ruth-AI integration"
    python scripts/manage_api_keys.py list
    python scripts/manage_api_keys.py revoke <api_key_id>
    python scripts/manage_api_keys.py activate <api_key_id>
"""
import asyncio
import sys
import os
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database import AsyncSessionLocal
from app.models.api_key import ApiKey
import secrets


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_hex(32)


async def create_api_key(name: str, description: str = None, expires_at: datetime = None):
    """Create a new API key."""
    async with AsyncSessionLocal() as db:
        # Generate the key
        key = generate_api_key()

        # Create database record
        api_key = ApiKey(
            key=key,
            name=name,
            description=description,
            expires_at=expires_at,
            is_active=True
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        print("\n✅ API Key created successfully!")
        print(f"ID: {api_key.id}")
        print(f"Name: {api_key.name}")
        print(f"Key: {key}")
        print(f"Created: {api_key.created_at}")

        if description:
            print(f"Description: {description}")
        if expires_at:
            print(f"Expires: {expires_at}")

        print("\n⚠️  IMPORTANT: Save this API key securely. You won't be able to retrieve it again!")
        print(f"\nTo use this key, set environment variable:")
        print(f'VAS_API_KEY="{key}"')
        print("\nOr include it in your requests:")
        print(f'curl -H "X-API-Key: {key}" http://localhost:8080/api/v1/devices')


async def list_api_keys(include_inactive: bool = False):
    """List all API keys."""
    async with AsyncSessionLocal() as db:
        query = select(ApiKey)

        if not include_inactive:
            query = query.where(ApiKey.is_active == True)

        query = query.order_by(ApiKey.created_at.desc())
        result = await db.execute(query)
        api_keys = result.scalars().all()

        if not api_keys:
            print("\nNo API keys found.")
            return

        print(f"\n{'='*100}")
        print(f"{'ID':<38} {'Name':<20} {'Active':<8} {'Created':<20} {'Last Used':<20}")
        print(f"{'='*100}")

        for key in api_keys:
            active_symbol = "✅" if key.is_active else "❌"
            last_used = key.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if key.last_used_at else "Never"
            created = key.created_at.strftime("%Y-%m-%d %H:%M:%S")

            print(f"{str(key.id):<38} {key.name:<20} {active_symbol:<8} {created:<20} {last_used:<20}")

            if key.description:
                print(f"  Description: {key.description}")
            if key.expires_at:
                expires = key.expires_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  Expires: {expires}")
            print()


async def revoke_api_key(api_key_id: str):
    """Revoke (deactivate) an API key."""
    async with AsyncSessionLocal() as db:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            print(f"\n❌ API key with ID {api_key_id} not found.")
            return

        if not api_key.is_active:
            print(f"\n⚠️  API key '{api_key.name}' is already revoked.")
            return

        api_key.is_active = False
        await db.commit()

        print(f"\n✅ API key '{api_key.name}' revoked successfully!")


async def activate_api_key(api_key_id: str):
    """Activate a previously revoked API key."""
    async with AsyncSessionLocal() as db:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            print(f"\n❌ API key with ID {api_key_id} not found.")
            return

        if api_key.is_active:
            print(f"\n⚠️  API key '{api_key.name}' is already active.")
            return

        api_key.is_active = True
        await db.commit()

        print(f"\n✅ API key '{api_key.name}' activated successfully!")


async def show_details(api_key_id: str):
    """Show details of a specific API key."""
    async with AsyncSessionLocal() as db:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            print(f"\n❌ API key with ID {api_key_id} not found.")
            return

        print(f"\n{'='*60}")
        print(f"API Key Details")
        print(f"{'='*60}")
        print(f"ID: {api_key.id}")
        print(f"Name: {api_key.name}")
        print(f"Active: {'✅ Yes' if api_key.is_active else '❌ No'}")
        print(f"Created: {api_key.created_at}")
        print(f"Updated: {api_key.updated_at or 'Never'}")
        print(f"Last Used: {api_key.last_used_at or 'Never'}")

        if api_key.description:
            print(f"Description: {api_key.description}")
        if api_key.expires_at:
            print(f"Expires: {api_key.expires_at}")
            if api_key.expires_at < datetime.now(api_key.expires_at.tzinfo):
                print("⚠️  This key has EXPIRED!")

        print(f"{'='*60}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage VAS API keys")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("--name", required=True, help="Name for the API key")
    create_parser.add_argument("--description", help="Description of the API key")

    # List command
    list_parser = subparsers.add_parser("list", help="List all API keys")
    list_parser.add_argument("--all", action="store_true", help="Include inactive keys")

    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("api_key_id", help="ID of the API key to revoke")

    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate an API key")
    activate_parser.add_argument("api_key_id", help="ID of the API key to activate")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show API key details")
    show_parser.add_argument("api_key_id", help="ID of the API key to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute commands
    if args.command == "create":
        asyncio.run(create_api_key(args.name, args.description))
    elif args.command == "list":
        asyncio.run(list_api_keys(include_inactive=args.all))
    elif args.command == "revoke":
        asyncio.run(revoke_api_key(args.api_key_id))
    elif args.command == "activate":
        asyncio.run(activate_api_key(args.api_key_id))
    elif args.command == "show":
        asyncio.run(show_details(args.api_key_id))


if __name__ == "__main__":
    main()
