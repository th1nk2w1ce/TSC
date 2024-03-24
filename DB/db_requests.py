from DB.models import User, async_session
from sqlalchemy import select


async def get_first_lvl_referrals(ref_id: int):
    async with async_session() as session:
        scal = await session.scalars(select(User.user_id).where(User.referrer == ref_id))
        res = 0
        for sc in scal:
            res += 1
        return res


class Storage:
    def __init__(self, user_id: int):
        self.user_id = user_id


    async def get_user(self):
        async with async_session() as session:
            scal = await session.scalar(select(User).where(User.user_id == self.user_id))
            try:
                return scal.referrer, scal.all_referrals, scal.referrer_address
            except:
                return False

    
    async def add_user(self, ref_id: int, ref_address: str):
        async with async_session() as session:
            user = User(user_id=self.user_id, referrer=ref_id, referrer_address=ref_address)
            session.add(user)
            await session.commit()

    
    async def update_referrals(self):
        async with async_session() as session:
            user = await session.get(User, self.user_id)
            user.all_referrals += 1
            await session.commit()
