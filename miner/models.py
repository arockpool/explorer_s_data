from django.db import models


class Miner(models.Model):
    '''
    矿工表
    '''
    miner_no = models.CharField('矿工no', max_length=128, db_index=True)
    miner_address = models.CharField('矿工地址', max_length=128, db_index=True, null=True)
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    sector_size = models.DecimalField('扇区大小', max_digits=24, decimal_places=0, default=0)
    total_sector = models.IntegerField('总的扇区数', default=0)
    active_sector = models.IntegerField('有效的扇区数', default=0)
    faulty_sector = models.IntegerField('错误的扇区数', default=0)
    recovering_sector = models.IntegerField('恢复中的扇区数', default=0)
    join_time = models.DateTimeField('加入时间', null=True)
    balance = models.DecimalField('余额', max_digits=34, decimal_places=0, default=0)
    available_balance = models.DecimalField('可用余额', max_digits=34, decimal_places=0, default=0)
    pledge_balance = models.DecimalField('质押总额', max_digits=34, decimal_places=0, default=0)
    initial_pledge_balance = models.DecimalField('扇区抵押额', max_digits=34, decimal_places=0, default=0)
    locked_pledge_balance = models.DecimalField('挖矿锁仓额', max_digits=34, decimal_places=0, default=0)
    total_reward = models.DecimalField('累计出块奖励', max_digits=34, decimal_places=0, default=0)
    total_block_count = models.IntegerField('累计出块数量', default=0)
    total_win_count = models.IntegerField('累计赢票数量', default=0)
    ip = models.CharField('ip', max_length=128, null=True)
    peer_id = models.CharField('peer_id', max_length=128, null=True)
    worker = models.CharField('worker', max_length=128, null=True)
    worker_balance = models.DecimalField('worker余额', max_digits=34, decimal_places=0, default=0)
    worker_address = models.CharField('worker地址', max_length=128, null=True)
    owner = models.CharField('owner', max_length=128, null=True)
    owner_balance = models.DecimalField('owner余额', max_digits=34, decimal_places=0, default=0)
    owner_address = models.CharField('owner地址', max_length=128, null=True)
    poster = models.CharField('poster', max_length=128, null=True)
    poster_balance = models.DecimalField('poster余额', max_digits=34, decimal_places=0, default=0)
    poster_address = models.CharField('poster地址', max_length=128, null=True)
    account_type = models.CharField('账户类型', max_length=128, null=True)
    ranking = models.IntegerField('排名', default=0)
    is_pool = models.IntegerField('是否矿池的矿工', default=0)
    # 链上数据展示
    max_pieceSize = models.CharField('max_pieceSize', max_length=64, default="0")
    min_pieceSize = models.CharField('min_pieceSize', max_length=64, default="0")
    price = models.CharField('price', max_length=32, default="0")
    verified_price = models.CharField('verified_price', max_length=32, default="0")

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-power", "-create_time", ]


class MinerHotHistory(models.Model):
    '''矿工热表，只保留48小时数据'''
    id = models.BigAutoField(primary_key=True)
    miner_no = models.CharField('矿工no', max_length=128, db_index=True)
    record_time = models.DateTimeField('记录时间')
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    total_sector = models.IntegerField('总的扇区数', default=0)
    active_sector = models.IntegerField('有效的扇区数', default=0)
    faulty_sector = models.IntegerField('错误的扇区数', default=0)
    recovering_sector = models.IntegerField('恢复中的扇区数', default=0)
    sector_size = models.DecimalField('扇区大小', max_digits=24, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-record_time", ]


class MinerDayStat(models.Model):
    '''24小时状态统计'''
    miner = models.OneToOneField(Miner, related_name="miner_day_stat", on_delete=models.DO_NOTHING)
    increase_power = models.DecimalField('24h新增算力(封装量)', max_digits=34, decimal_places=0, default=0)
    increase_power_offset = models.DecimalField('24h算力增速', max_digits=34, decimal_places=0, default=0)
    avg_reward = models.DecimalField('24h平均挖矿收益 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    lucky = models.DecimalField('幸运值', max_digits=12, decimal_places=4, default=0)
    block_reward = models.DecimalField('出块奖励', max_digits=34, decimal_places=0, default=0)
    block_count = models.IntegerField('出块数量', default=0)
    win_count = models.IntegerField('赢票数量', default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-create_time", ]


class MinerDay(models.Model):

    date = models.DateField('时间', db_index=True)
    miner_no = models.CharField('矿工no', max_length=128, db_index=True)
    raw_power = models.DecimalField('原值算力', max_digits=34, decimal_places=0, default=0)
    power = models.DecimalField('有效算力', max_digits=34, decimal_places=0, default=0)
    sector_size = models.DecimalField('扇区大小', max_digits=24, decimal_places=0, default=0)
    total_sector = models.IntegerField('总的扇区数', default=0)
    active_sector = models.IntegerField('有效的扇区数', default=0)
    faulty_sector = models.IntegerField('错误的扇区数', default=0)
    recovering_sector = models.IntegerField('恢复中的扇区数', default=0)
    new_sector = models.IntegerField('新增的扇区数', default=0)
    balance = models.DecimalField('余额', max_digits=34, decimal_places=0, default=0)
    available_balance = models.DecimalField('可用余额', max_digits=34, decimal_places=0, default=0)
    pledge_balance = models.DecimalField('质押余额', max_digits=34, decimal_places=0, default=0)
    initial_pledge_balance = models.DecimalField('扇区抵押额', max_digits=34, decimal_places=0, default=0)
    locked_pledge_balance = models.DecimalField('挖矿锁仓额', max_digits=34, decimal_places=0, default=0)
    total_reward = models.DecimalField('累计出块奖励', max_digits=34, decimal_places=0, default=0)
    total_block_count = models.IntegerField('累计出块数量', default=0)
    total_win_count = models.IntegerField('累计赢票数量', default=0)
    increase_power = models.DecimalField('新增算力', max_digits=34, decimal_places=0, default=0)
    increase_power_offset = models.DecimalField('新增算力差值', max_digits=34, decimal_places=0, default=0)
    pre_gas = models.DecimalField('pre_gas费', max_digits=34, decimal_places=0, default=0)
    pre_gas_count = models.IntegerField('pre_gas次数', default=0)
    prove_gas = models.DecimalField('prove_gas', max_digits=34, decimal_places=0, default=0)
    prove_gas_count = models.IntegerField('prove_gas次数', default=0)
    win_post_gas = models.DecimalField('win_post_gas费', max_digits=34, decimal_places=0, default=0)
    win_post_gas_count = models.IntegerField('win_post_gas', default=0)
    pledge_gas = models.DecimalField('质押gas', max_digits=34, decimal_places=0, default=0)
    avg_reward = models.DecimalField('24h平均挖矿收益 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    lucky = models.DecimalField('幸运值', max_digits=12, decimal_places=4, default=0)
    block_reward = models.DecimalField('出块奖励', max_digits=34, decimal_places=0, default=0)
    block_count = models.IntegerField('出块数量', default=0)
    win_count = models.IntegerField('赢票数量', default=0)
    worker = models.CharField('worker', max_length=128, null=True, db_index=True)
    worker_balance = models.DecimalField('worker余额', max_digits=34, decimal_places=0, default=0)
    worker_address = models.CharField('worker地址', max_length=128, null=True, db_index=True)
    owner = models.CharField('owner', max_length=128, null=True, db_index=True)
    owner_balance = models.DecimalField('owner余额', max_digits=34, decimal_places=0, default=0)
    owner_address = models.CharField('owner地址', max_length=128, null=True, db_index=True)
    poster = models.CharField('poster', max_length=128, null=True, db_index=True)
    poster_balance = models.DecimalField('poster余额', max_digits=34, decimal_places=0, default=0)
    poster_address = models.CharField('poster地址', max_length=128, null=True, db_index=True)
    overtime_pledge_fee = models.DecimalField('过期质押', max_digits=34, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-date", "-create_time", ]


class MinerSyncLog(models.Model):
    '''同步日志'''
    date = models.DateField('时间', db_index=True)
    gas_sync_height = models.IntegerField('gas费同步到的高度', default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-date", "-create_time", ]


class Company(models.Model):
    '''矿商'''
    code = models.CharField('矿商code', max_length=128)
    name = models.CharField('矿商名称', max_length=128, null=True)
    join_time = models.DateTimeField('加入时间', null=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-create_time", ]


class CompanyMiner(models.Model):
    '''矿商矿工'''
    company = models.ForeignKey(Company, related_name="miners", on_delete=models.DO_NOTHING)
    miner_no = models.CharField('矿工no', max_length=128)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-create_time", ]
