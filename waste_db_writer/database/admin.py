from django.contrib import admin
from .models import PlantInfo
from .models import EdgeBoxInfo
from .models import WasteSegments
from .models import WasteImpurity
from .models import WasteMaterial
from .models import WasteDust, WasteHotSpot
from .models import WasteFeedback

class PlantInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant_id', 'plant_name', 'plant_location', 'created_at', 'meta_info']

class EdgeBoxInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant', 'edge_box_id', 'edge_box_location', 'created_at', 'meta_info']
    
class WasteSegmentsAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'created_at', 'object_uid', 
        'object_tracker_id', 'confidence_score', 'object_area', 
        'object_length', 'img_id', 'img_file', 'model_name', 'model_tag'
    )
    search_fields = ('object_uid', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at')


class WasteImpurityAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'created_at', 'object_uid', 
        'object_tracker_id', 'is_long', 'is_problematic', 
        'confidence_score', 'severity_level', 'model_name', 'model_tag'
    )
    search_fields = ('object_uid', 'severity_level', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at', 'is_long', 'is_problematic', 'severity_level')
    
class WasteMaterialAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'created_at', 'object_uid', 
        'object_tracker_id', 'object_material_type', 'confidence_score', 
        'model_name', 'model_tag'
    )
    search_fields = ('object_uid', 'object_material_type', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at', 'object_material_type')
    ordering = ('-timestamp',)

class WasteDustAdmin(admin.ModelAdmin):
    list_display = ('event_uid', 'edge_box', 'timestamp', 'confidence_score', 'severity_level', 'model_name', 'model_tag')
    search_fields = ('event_uid__id', 'edge_box__name', 'model_name', 'model_tag')
    list_filter = ('severity_level', 'model_name', 'model_tag')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at',)

class WasteHotSpotAdmin(admin.ModelAdmin):
    list_display = ('event_uid', 'edge_box', 'timestamp', 'confidence_score', 'severity_level', 'model_name', 'model_tag')
    search_fields = ('event_uid__id', 'edge_box__name', 'model_name', 'model_tag')
    list_filter = ('severity_level', 'model_name', 'model_tag')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at',)
    
    
class WasteFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_uid', 'event', 'created_at', 'updated_at', 'user_id', 'ack_status', 'comment', 'rating')
    search_fields = ('event_uid', 'event', 'user_id', 'comment')
    list_filter = ('ack_status', 'rating', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('event_uid', 'event', 'user_id', 'ack_status', 'comment', 'rating', 'meta_info')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Register your models here.
admin.site.register(PlantInfo, PlantInfoAdmin)
admin.site.register(EdgeBoxInfo, EdgeBoxInfoAdmin)
admin.site.register(WasteSegments, WasteSegmentsAdmin)
admin.site.register(WasteImpurity, WasteImpurityAdmin)
admin.site.register(WasteMaterial, WasteMaterialAdmin)
admin.site.register(WasteDust, WasteDustAdmin)
admin.site.register(WasteHotSpot, WasteHotSpotAdmin)
admin.site.register(WasteFeedback, WasteFeedbackAdmin)