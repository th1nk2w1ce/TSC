from DB.models import User, async_session
from sqlalchemy import select


async def get_first_lvl_referrals(ref_id: int):
    async with async_session() as session:
        scal = await session.scalars(select(User.tg_id).where(User.referer == ref_id))
        res = 0
        for sc in scal:
            res += 1
        return res


class Storage:
    def __init__(self, tg_id: int):
        self.tg_id = tg_id


    async def get_user(self):
        async with async_session() as session:
            scal = await session.scalar(select(User).where(User.tg_id == self.tg_id))
            try:
                return scal.referer, scal.all_referals, scal.referer_address
            except:
                return False

    
    async def add_user(self, ref_id: int, ref_address: str):
        async with async_session() as session:
            user = User(tg_id=self.tg_id, referer=ref_id, referer_address=ref_address)
            session.add(user)
            await session.commit()

    
    async def update_referrals(self):
        async with async_session() as session:
            user = await session.get(User, self.tg_id)
            user.all_referals += 1
            await session.commit()
