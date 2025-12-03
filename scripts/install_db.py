#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime, timezone

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.motor_database import motor_db_manager
from app.core.constants import DEFAULT_PERMISSIONS, DEFAULT_ROLES, DEFAULT_GROUPS
from app.core.security import get_password_hash


async def ensure_permissions(db):
    perms_col = db["permissions"]
    created = 0
    for name, description in DEFAULT_PERMISSIONS.items():
        existing = await perms_col.find_one({"name": name})
        
        # Derive resource and action from name
        if ":" in name:
            resource, action = name.split(":", 1)
        else:
            resource = "system"
            action = name
            
        if not existing:
            await perms_col.insert_one({
                "name": name,
                "description": description,
                "resource": resource,
                "action": action,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            created += 1
        else:
            # Ensure resource and action are set even if permission exists
            if "resource" not in existing or "action" not in existing:
                await perms_col.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"resource": resource, "action": action}}
                )
    print(f"permissions: created={created}")


async def ensure_roles(db):
    roles_col = db["roles"]
    perms_col = db["permissions"]
    created = 0
    for role_name, role_data in DEFAULT_ROLES.items():
        existing = await roles_col.find_one({"name": role_name})
        # Resolve permission ids
        perm_ids = []
        for perm_name in role_data.get("permissions", []):
            perm = await perms_col.find_one({"name": perm_name}, {"_id": 1})
            if perm:
                perm_ids.append(perm["_id"])
        if not existing:
            doc = {
                "name": role_name,
                "description": role_data.get("description", ""),
                "permission_ids": perm_ids,
                "is_system_role": role_data.get("is_system_role", False),
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await roles_col.insert_one(doc)
            created += 1
        else:
            # Update to ensure permission_ids field is present and correct
            await roles_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"permission_ids": perm_ids, "updated_at": datetime.now(timezone.utc)}, "$unset": {"permissions": ""}}
            )
    print(f"roles: created={created}")


async def ensure_groups(db):
    groups_col = db["groups"]
    created = 0
    for group_name, group_data in DEFAULT_GROUPS.items():
        existing = await groups_col.find_one({"name": group_name})
        if not existing:
            doc = {
                "name": group_name,
                "description": group_data.get("description", ""),
                "is_system_group": group_data.get("is_system_group", False),
                "metadata": group_data.get("metadata", {}),
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await groups_col.insert_one(doc)
            created += 1
    print(f"groups: created={created}")


async def ensure_admin_user(db):
    users = db["users"]
    admin_email = "admin@example.com"
    existing = await users.find_one({"email": admin_email})
    if existing:
        print("admin user already exists")
        # ensure role/group membership
        await assign_admin_memberships(db, existing["_id"])
        return
    hashed = get_password_hash("password123")
    doc = {
        "username": "admin",
        "email": admin_email,
        "hashed_password": hashed,
        "is_active": True,
        "is_superuser": False,
        "email_verified": True,
        "profile": {"full_name": "Admin User"},
        "preferences": {"theme": "light", "language": "en", "timezone": "UTC"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "role_ids": [],
        "group_ids": []
    }
    result = await users.insert_one(doc)
    print(f"admin user created id={result.inserted_id}")
    await assign_admin_memberships(db, result.inserted_id)


async def assign_admin_memberships(db, user_id):
    roles_col = db["roles"]
    groups_col = db["groups"]
    users_col = db["users"]
    superadmin_role = await roles_col.find_one({"name": "superadmin"}, {"_id": 1})
    administrators_group = await groups_col.find_one({"name": "administrators"}, {"_id": 1})
    updates = {}
    if superadmin_role:
        updates.setdefault("$addToSet", {}).setdefault("role_ids", superadmin_role["_id"])
    if administrators_group:
        updates.setdefault("$addToSet", {}).setdefault("group_ids", administrators_group["_id"])
    if updates:
        await users_col.update_one({"_id": user_id}, updates)
        print("admin memberships ensured (role/group)")


async def main():
    await motor_db_manager.connect()
    try:
        db = motor_db_manager.database
        await ensure_permissions(db)
        await ensure_roles(db)
        await ensure_groups(db)
        await ensure_admin_user(db)
        # Simple indexes
        await db["users"].create_index("email", unique=True)
        await db["users"].create_index("username", unique=True)
        await db["permissions"].create_index("name", unique=True)
        await db["roles"].create_index("name", unique=True)
        await db["groups"].create_index("name", unique=True)
        print("indexes ensured")
    finally:
        await motor_db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())