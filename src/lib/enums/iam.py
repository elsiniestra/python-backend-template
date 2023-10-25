from src.lib.enums.base import BaseEnum


class IAMUserGroup(BaseEnum):
    SUPERADMIN = "superadmin"
    EDITOR = "editor"


class IAMScope(BaseEnum):
    ADMIN_USERS = "admin_users"
    ADMIN_POSTS = "admin_posts"
    ADMIN_STATS = "admin_stats"


class IAMAccess(BaseEnum):
    READ = "read"
    WRITE = "write"
