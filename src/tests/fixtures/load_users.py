from src.injected import DomainHolder
from src.lib import enums, schemas


async def load_users(domain_holder: DomainHolder) -> None:
    await domain_holder.user.controller.create(
        item=schemas.UserCreate(
            first_name="Test",
            last_name="Test",
            username="testuser",
            email="user@test.com",
            password="testpassword",
        )
    )

    admin = await domain_holder.user.controller.create(
        item=schemas.UserCreate(
            first_name="Admin",
            last_name="Admin",
            username="admin",
            email="admin@admin.com",
            password="admin",
        )
    )

    await domain_holder.user.controller.assign_group(
        item_id=admin.id,
        item=schemas.IAMGroupToUserAssign(
            user_group=enums.IAMUserGroup.SUPERADMIN,
        ),
    )
