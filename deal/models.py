from django.db import models


class Deal(models.Model):
    '''
    订单表
    '''
    deal_id = models.BigIntegerField('订单id', default=0, db_index=True)
    piece_cid = models.CharField('文件cid', max_length=128, db_index=True, null=True)
    piece_size = models.DecimalField('文件大小', max_digits=34, decimal_places=0, default=0)
    is_verified = models.IntegerField('是否已验证', default=0)
    client = models.CharField('客户', max_length=128, null=True)
    provider = models.CharField('托管矿工', max_length=128, null=True)
    start_epoch = models.IntegerField('存储开始高度', default=0)
    end_epoch = models.IntegerField('存储结束高度', default=0)
    storage_price_per_epoch = models.DecimalField('每高度每byte单价', max_digits=34, decimal_places=0, default=0)
    provider_collateral = models.DecimalField('托管矿工抵押', max_digits=34, decimal_places=0, default=0)
    client_collateral = models.DecimalField('客户抵押', max_digits=34, decimal_places=0, default=0)
    sector_start_epoch = models.IntegerField('接单高度', default=0)
    last_updated_epoch = models.IntegerField('最近更新高度', default=0)
    slash_epoch = models.IntegerField('丢弃高度', default=0)

    height = models.IntegerField('订单创建高度', default=0, db_index=True)
    record_time = models.DateTimeField('记录时间', null=True, db_index=True)
    # block_id = models.CharField('区块ID', max_length=128, null=True)
    msg_cid = models.CharField('消息CID', max_length=128, null=True)
    # storage_fee = models.DecimalField('存储费用', max_digits=34, decimal_places=0, default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-deal_id", "-create_time", ]
