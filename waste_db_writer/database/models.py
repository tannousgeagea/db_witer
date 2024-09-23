from django.db import models

# Create your models here.
class PlantInfo(models.Model):
    plant_id = models.CharField(max_length=255)
    plant_name = models.CharField(max_length=255)
    plant_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'plant_info'
        verbose_name_plural = 'Plant Information'    


    def __str__(self):
        return f"{self.plant_id}"
        
class EdgeBoxInfo(models.Model):
    plant = models.ForeignKey(PlantInfo, on_delete=models.CASCADE)
    edge_box_id = models.CharField(max_length=255)
    edge_box_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info =  models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'edge_box_info'
        verbose_name_plural = 'EdgeBox Information'
    
    def __str__(self):
        return f'{self.edge_box_id}'
    

class WasteSegments(models.Model):
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    object_uid = models.CharField(max_length=255)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    object_tracker_id = models.IntegerField()
    object_polygon = models.JSONField()
    confidence_score = models.FloatField(max_length=100)
    object_area = models.FloatField(max_length=100)
    object_length = models.FloatField(max_length=100)
    img_id = models.CharField(max_length=255, null=True, blank=True)
    img_file = models.CharField(max_length=255, null=True, blank=True)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)


    class Meta: 
        db_table = 'waste_segments'
        verbose_name_plural = 'Waste Segments'
        
    def __str__(self):
        return f"{self.object_uid}"

class WasteImpurity(models.Model):
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    object_uid = models.OneToOneField(WasteSegments, on_delete=models.CASCADE)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    object_tracker_id = models.IntegerField()
    is_long = models.BooleanField(default=False)
    is_problematic = models.BooleanField(default=False)
    confidence_score = models.FloatField()
    severity_level = models.IntegerField()
    object_coordinates = models.JSONField(null=True, blank=True)
    img_id = models.CharField(max_length=255)
    img_file = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_impurity'
        verbose_name_plural = 'Waste Impurity'
        
    def __str__(self):
        return f"{self.object_uid.object_uid}: {self.object_uid.object_length}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        WasteAlarm.objects.create(
            event='impurity',
            edge_box=self.edge_box,
            timestamp=self.timestamp,
            event_uid=self.event_uid,
            delivery_id=self.delivery_id,
            confidence_score=self.confidence_score,
            severity_level=self.severity_level,
            img_id=self.img_id,
            img_file=self.img_file,
            model_name=self.model_name,
            model_tag=self.model_tag,
            meta_info=self.meta_info,
        )
    
class WasteMaterial(models.Model):
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    object_uid = models.OneToOneField(WasteSegments, on_delete=models.CASCADE)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    object_tracker_id = models.IntegerField()
    object_material_type = models.CharField(max_length=255)
    confidence_score = models.FloatField()
    img_id = models.CharField(max_length=255)
    img_file = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_material'
        verbose_name_plural = 'Waste Material'
        
    def __str__(self):
        return f"{self.object_uid.object_uid}: {self.object_material_type}"
    

class WasteDust(models.Model):
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField()
    severity_level = models.IntegerField()
    img_id = models.CharField(max_length=255)
    img_file = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_dust'
        verbose_name_plural = 'Waste Dust'
        
    def __str__(self):
        return f"dust {self.event_uid} at {self.edge_box}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        WasteAlarm.objects.create(
            event='dust',
            edge_box=self.edge_box,
            timestamp=self.timestamp,
            event_uid=self.event_uid,
            delivery_id=self.delivery_id,
            confidence_score=self.confidence_score,
            severity_level=self.severity_level,
            img_id=self.img_id,
            img_file=self.img_file,
            model_name=self.model_name,
            model_tag=self.model_tag,
            meta_info=self.meta_info,
        )
    

class WasteHotSpot(models.Model):
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField()
    severity_level = models.IntegerField()
    img_id = models.CharField(max_length=255)
    img_file = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_hostspot'
        verbose_name_plural = 'Waste HotSpot'
        
    def __str__(self):
        return f"hotspot {self.event_uid} at {self.edge_box}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        WasteAlarm.objects.create(
            event='hotspot',
            edge_box=self.edge_box,
            timestamp=self.timestamp,
            event_uid=self.event_uid,
            delivery_id=self.delivery_id,
            confidence_score=self.confidence_score,
            severity_level=self.severity_level,
            img_id=self.img_id,
            img_file=self.img_file,
            model_name=self.model_name,
            model_tag=self.model_tag,
            meta_info=self.meta_info,
        )
    
class WasteAlarm(models.Model):
    event = models.CharField(max_length=100)
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_uid = models.CharField(max_length=255)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField()
    severity_level = models.IntegerField()
    img_id = models.CharField(max_length=255)
    img_file = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_tag = models.CharField(max_length=255)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_alar,'
        verbose_name_plural = 'Waste Alarm'
        
    def __str__(self):
        return f"{self.event} {self.event_uid} at {self.edge_box}"
    
class WasteFeedback(models.Model):
    event_uid = models.CharField(max_length=255)
    event = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()
    user_id = models.CharField(max_length=255, null=True, blank=True)
    ack_status = models.BooleanField()
    comment = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField()
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'waste_feedback'
        verbose_name = 'Waste Feedback'
        verbose_name_plural = 'Waste Feedbacks'

    def __str__(self):
        return f"{self.event} created at {self.created_at}"
    

