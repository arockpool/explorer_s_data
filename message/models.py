from django.db import models


class TipsetGasSum(models.Model):
    '''
    每个高度的gas费汇总，统计base_gas、pre_fas、prov_gas、win_post_gas，用于计算生成成本、维护成本
    '''
    height = models.IntegerField('高度', default=0, db_index=True)
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    pre_gas = models.DecimalField('pre_gas费', max_digits=34, decimal_places=0, default=0)
    pre_gas_count = models.IntegerField('pre_gas次数', default=0)
    prove_gas = models.DecimalField('prove_gas', max_digits=34, decimal_places=0, default=0)
    prove_gas_count = models.IntegerField('prove_gas次数', default=0)
    win_post_gas = models.DecimalField('win_post_gas费', max_digits=34, decimal_places=0, default=0)
    win_post_gas_count = models.IntegerField('win_post_gas次数', default=0)
    base_fee = models.DecimalField('base_fee', max_digits=34, decimal_places=0, default=0)
    create_gas_32 = models.DecimalField('32G生产gas', max_digits=34, decimal_places=18, default=0)
    keep_gas_32 = models.DecimalField('32G维护gas', max_digits=34, decimal_places=18, default=0)
    create_gas_64 = models.DecimalField('64G生产gas', max_digits=34, decimal_places=18, default=0)
    keep_gas_64 = models.DecimalField('64G维护gas', max_digits=34, decimal_places=18, default=0)

    pre_gas_32 = models.DecimalField('32pre_gas费', max_digits=34, decimal_places=0, default=0)
    pre_gas_count_32 = models.IntegerField('32pre_gas次数', default=0)
    prove_gas_32 = models.DecimalField('32prove_gas', max_digits=34, decimal_places=0, default=0)
    prove_gas_count_32 = models.IntegerField('32prove_gas次数', default=0)
    win_post_gas_32 = models.DecimalField('32win_post_gas费', max_digits=34, decimal_places=0, default=0)
    win_post_gas_count_32 = models.IntegerField('32win_post_gas次数', default=0)
    pre_gas_64 = models.DecimalField('64pre_gas费', max_digits=34, decimal_places=0, default=0)
    pre_gas_count_64 = models.IntegerField('64pre_gas次数', default=0)
    prove_gas_64 = models.DecimalField('64prove_gas', max_digits=34, decimal_places=0, default=0)
    prove_gas_count_64 = models.IntegerField('64prove_gas次数', default=0)
    win_post_gas_64 = models.DecimalField('64win_post_gas费', max_digits=34, decimal_places=0, default=0)
    win_post_gas_count_64 = models.IntegerField('64win_post_gas次数', default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-height", "-create_time", ]


class TipsetGasStat(models.Model):
    '''24小时内每个tipset的各种gas费汇总'''
    sector_type_choices = ((0, '32 GiB'), (1, '64 GiB'),)

    height = models.IntegerField('高度', default=0, db_index=True)
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    sector_type = models.IntegerField(verbose_name="扇区类型", choices=sector_type_choices, default=0)
    method = models.CharField('gas方法', max_length=128, db_index=True)
    count = models.IntegerField('次数', default=0)
    gas_limit = models.DecimalField('gas_limit汇总', max_digits=34, decimal_places=0, default=0)
    gas_fee_cap = models.DecimalField('gas_fee_cap汇总', max_digits=34, decimal_places=0, default=0)
    gas_premium = models.DecimalField('gas_premium汇总', max_digits=34, decimal_places=0, default=0)
    gas_used = models.DecimalField('gas_used汇总', max_digits=34, decimal_places=0, default=0)
    base_fee_burn = models.DecimalField('base_fee_burn汇总', max_digits=34, decimal_places=0, default=0)
    total_cost = models.DecimalField('total_cost汇总', max_digits=34, decimal_places=0, default=0)
    msg_value = models.DecimalField('消息金额', max_digits=34, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-height", "-create_time", ]


class PoolTipsetGasStat(models.Model):
    '''矿池24小时内每个tipset的各种gas费汇总'''
    sector_type_choices = ((0, '32 GiB'), (1, '64 GiB'),)

    height = models.IntegerField('高度', default=0, db_index=True)
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    sector_type = models.IntegerField(verbose_name="扇区类型", choices=sector_type_choices, default=0)
    method = models.CharField('gas方法', max_length=128, db_index=True)
    count = models.IntegerField('次数', default=0)
    gas_limit = models.DecimalField('gas_limit汇总', max_digits=34, decimal_places=0, default=0)
    gas_fee_cap = models.DecimalField('gas_fee_cap汇总', max_digits=34, decimal_places=0, default=0)
    gas_premium = models.DecimalField('gas_premium汇总', max_digits=34, decimal_places=0, default=0)
    gas_used = models.DecimalField('gas_used汇总', max_digits=34, decimal_places=0, default=0)
    base_fee_burn = models.DecimalField('base_fee_burn汇总', max_digits=34, decimal_places=0, default=0)
    total_cost = models.DecimalField('total_cost汇总', max_digits=34, decimal_places=0, default=0)
    msg_value = models.DecimalField('消息金额', max_digits=34, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-height", "-create_time", ]


class PledgeHistory(models.Model):
    """质押48小时内的数据"""
    miner_no = models.CharField('矿工no', max_length=128, db_index=True)
    height = models.IntegerField('高度', default=0, db_index=True, )
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    sector_number = models.BigIntegerField('扇区编号', default=0, db_index=True)
    value = models.DecimalField('金额', max_digits=34, decimal_places=0, default=0)
    method = models.CharField('方法', max_length=32)
    msg_id = models.CharField('msg_id', max_length=128, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-height", "-create_time", ]


class OvertimePledge(models.Model):
    """过期质押"""
    miner_no = models.CharField('矿工no', max_length=128, db_index=True)
    height = models.IntegerField('高度', default=0, db_index=True, )
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    msg_id = models.CharField('msg_id', max_length=128, null=True, db_index=True)
    sector_number = models.BigIntegerField('扇区编号', default=0, db_index=True)
    value = models.DecimalField('金额', max_digits=34, decimal_places=0, default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-height", "-create_time", ]