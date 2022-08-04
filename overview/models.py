from django.db import models


class Overview(models.Model):
    '''
    预览表
    '''
    record_time = models.DateTimeField('记录时间', db_index=True)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    height = models.IntegerField('全网区块高度', default=0)
    reward = models.DecimalField('全网总区块奖励', max_digits=34, decimal_places=0, default=0)
    block_count = models.IntegerField('全网出块数', default=0)
    block_reward = models.DecimalField('最新区块奖励', max_digits=34, decimal_places=0, default=0)
    active_miner_count = models.IntegerField('活跃矿工数', default=0)
    account_count = models.IntegerField('总账户数', default=0)
    avg_pledge = models.DecimalField('当前扇区质押量', max_digits=8, decimal_places=4, default=0)
    avg_reward = models.DecimalField('24小时平均挖矿收益', max_digits=8, decimal_places=4, default=0)
    circulating_supply = models.DecimalField('流通量', max_digits=34, decimal_places=0, default=0)
    base_fee = models.DecimalField('基础费率', max_digits=34, decimal_places=0, default=0)
    burnt_supply = models.DecimalField('销毁量', max_digits=34, decimal_places=0, default=0)
    msg_count = models.IntegerField('24小时消息数', default=0)
    total_pledge = models.DecimalField('挖矿质押总和', max_digits=34, decimal_places=0, default=0)
    price = models.DecimalField('fil价格', max_digits=10, decimal_places=4, default=0)
    price_change = models.DecimalField('fil价格变化量', max_digits=10, decimal_places=4, default=0)
    avg_tipset_blocks = models.DecimalField('平均区块高度', max_digits=10, decimal_places=4, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-record_time", "-create_time", ]


class OverviewDay(models.Model):
    '''
    每日预览表
    '''
    date = models.DateField('时间', db_index=True)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    height = models.IntegerField('全网区块高度', default=0)
    reward = models.DecimalField('全网总区块奖励', max_digits=34, decimal_places=0, default=0)
    block_count = models.IntegerField('全网出块数', default=0)
    block_reward = models.DecimalField('最新区块奖励', max_digits=34, decimal_places=0, default=0)
    active_miner_count = models.IntegerField('活跃矿工数', default=0)
    account_count = models.IntegerField('总账户数', default=0)
    avg_pledge = models.DecimalField('当前扇区质押量', max_digits=8, decimal_places=4, default=0)
    avg_reward = models.DecimalField('24小时平均挖矿收益', max_digits=8, decimal_places=4, default=0)
    circulating_supply = models.DecimalField('流通量', max_digits=34, decimal_places=0, default=0)
    base_fee = models.DecimalField('基础费率', max_digits=34, decimal_places=0, default=0)
    burnt_supply = models.DecimalField('销毁量', max_digits=34, decimal_places=0, default=0)
    msg_count = models.IntegerField('24小时消息数', default=0)
    total_pledge = models.DecimalField('挖矿质押总和', max_digits=34, decimal_places=0, default=0)
    price = models.DecimalField('fil价格', max_digits=10, decimal_places=4, default=0)
    price_change = models.DecimalField('fil价格变化量', max_digits=10, decimal_places=4, default=0)
    avg_tipset_blocks = models.DecimalField('平均区块高度', max_digits=10, decimal_places=4, default=0)
    increase_power = models.DecimalField('新增算力', max_digits=34, decimal_places=0, default=0)
    avg_base_fee = models.DecimalField('24小时平均基础费率', max_digits=34, decimal_places=0, default=0)
    create_gas_32 = models.DecimalField('32G生产gas', max_digits=34, decimal_places=0, default=0)
    create_gas_64 = models.DecimalField('64G生产gas', max_digits=34, decimal_places=0, default=0)
    keep_gas_32 = models.DecimalField('32G维护gas', max_digits=34, decimal_places=0, default=0)
    keep_gas_64 = models.DecimalField('64G维护gas', max_digits=34, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-date", "-create_time", ]


class OverviewPool(models.Model):
    '''
    矿池预览表
    '''
    record_time = models.DateTimeField('记录时间', db_index=True)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    total_sector = models.IntegerField('总的扇区数', default=0)
    active_sector = models.IntegerField('有效的扇区数', default=0)
    faulty_sector = models.IntegerField('错误的扇区数', default=0)
    recovering_sector = models.IntegerField('恢复中的扇区数', default=0)
    balance = models.DecimalField('余额', max_digits=34, decimal_places=0, default=0)
    available_balance = models.DecimalField('可用余额', max_digits=34, decimal_places=0, default=0)
    pledge_balance = models.DecimalField('质押余额', max_digits=34, decimal_places=0, default=0)
    total_reward = models.DecimalField('累计出块奖励', max_digits=34, decimal_places=0, default=0)
    total_block_count = models.IntegerField('累计出块数量', default=0)
    total_win_count = models.IntegerField('累计赢票数量', default=0)
    increase_power = models.DecimalField('新增算力offset', max_digits=34, decimal_places=0, default=0)
    increase_power_add = models.DecimalField('新增算力增量', max_digits=34, decimal_places=0, default=0)
    avg_reward = models.DecimalField('24h平均挖矿收益 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    lucky = models.DecimalField('幸运值', max_digits=8, decimal_places=4, default=0)
    count = models.IntegerField('矿工数量', default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-record_time", "-create_time", ]
