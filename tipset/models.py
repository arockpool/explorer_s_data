from django.db import models


class Tipset(models.Model):
    '''
    区块高度
    '''
    height = models.IntegerField('高度', default=0, db_index=True)
    total_win_count = models.IntegerField('总消息数量', default=0)
    total_block_count = models.IntegerField('总区块数量', default=0)
    total_reward = models.DecimalField('总区块奖励', max_digits=40, decimal_places=0, default=0)

    record_time = models.DateTimeField('产生时间', db_index=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-record_time", "-create_time", ]


class TipsetBlock(models.Model):
    '''
    区块
    '''
    tipset = models.ForeignKey('Tipset', related_name='blocks', on_delete=models.DO_NOTHING, null=True)
    height = models.IntegerField('高度', default=0, db_index=True)
    record_time = models.DateTimeField('产生时间', db_index=True)
    block_hash = models.CharField('消息hash', max_length=128, null=True, db_index=True)
    miner_no = models.CharField('矿工id', max_length=128, null=True, db_index=True)
    msg_count = models.IntegerField('消息数量', default=0)
    win_count = models.IntegerField('赢票数量', default=0)
    reward = models.DecimalField('区块奖励', max_digits=40, decimal_places=0, default=0)
    penalty = models.DecimalField('区块奖励', max_digits=40, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-record_time", "-create_time", ]


class TempTipsetBlock(models.Model):
    '''
    临时区块信息
    '''
    height = models.IntegerField('高度', default=0, db_index=True)
    record_time = models.DateTimeField('产生时间', db_index=True)
    block_hash = models.CharField('消息hash', max_length=128, null=True)
    miner_no = models.CharField('矿工id', max_length=128, null=True, db_index=True)
    msg_count = models.IntegerField('消息数量', default=0)
    win_count = models.IntegerField('赢票数量', default=0)
    reward = models.DecimalField('区块奖励', max_digits=40, decimal_places=0, default=0)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-record_time", "-create_time", ]
