
from django.contrib import admin
from .models import (
    PlantInfo, EdgeBoxInfo, WasteSegments, WasteImpurity, WasteMaterial, WasteDust, WasteHotSpot, WasteFeedback,
    Metadata, MetadataColumn, MetadataLocalization, Filter, FilterItem, FilterLocalization, FilterItemLocalization
)

# Existing Admin Configurations
@admin.register(PlantInfo)
class PlantInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant_id', 'plant_name', 'plant_location', 'created_at', 'meta_info']

@admin.register(EdgeBoxInfo)
class EdgeBoxInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant', 'edge_box_id', 'edge_box_location', 'created_at', 'meta_info']

@admin.register(WasteSegments)
class WasteSegmentsAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'object_uid', 
        'object_tracker_id', 'confidence_score_display', 'object_area_display', 
        'object_length_display', 'model_name', 'model_tag'
    )
    search_fields = ('object_uid', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at')

    def confidence_score_display(self, obj):
        return f"{obj.confidence_score:.2f}"
    confidence_score_display.short_description = 'Confidence Score'

    def object_area_display(self, obj):
        return f"{obj.object_area:.3f}"
    object_area_display.short_description = 'Object Area'

    def object_length_display(self, obj):
        return f"{obj.object_length:.2f}"
    object_length_display.short_description = 'Object Length'

@admin.register(WasteImpurity)
class WasteImpurityAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'created_at', 'object_uid', 
        'confidence_score', 'severity_level', 'model_name', 'model_tag'
    )
    search_fields = ('object_uid__object_uid', 'severity_level', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at', 'is_long', 'is_problematic', 'severity_level')

@admin.register(WasteMaterial)
class WasteMaterialAdmin(admin.ModelAdmin):
    list_display = (
        'edge_box', 'timestamp', 'created_at', 'object_uid', 
        'object_tracker_id', 'object_material_type', 'confidence_score', 
        'model_name', 'model_tag'
    )
    search_fields = ('object_uid', 'object_material_type', 'model_name', 'model_tag')
    list_filter = ('timestamp', 'created_at', 'object_material_type')
    ordering = ('-timestamp',)

@admin.register(WasteDust)
class WasteDustAdmin(admin.ModelAdmin):
    list_display = ('event_uid', 'edge_box', 'timestamp', 'confidence_score', 'severity_level', 'model_name', 'model_tag')
    search_fields = ('event_uid__id', 'edge_box__name', 'model_name', 'model_tag')
    list_filter = ('severity_level', 'model_name', 'model_tag')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at',)

@admin.register(WasteHotSpot)
class WasteHotSpotAdmin(admin.ModelAdmin):
    list_display = ('event_uid', 'edge_box', 'timestamp', 'confidence_score', 'severity_level', 'model_name', 'model_tag')
    search_fields = ('event_uid__id', 'edge_box__name', 'model_name', 'model_tag')
    list_filter = ('severity_level', 'model_name', 'model_tag')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at',)

@admin.register(WasteFeedback)
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

# New Models Admin Configurations
@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ('primary_key', 'description')
    search_fields = ('primary_key', 'description')
    
    class MetadataColumnInline(admin.TabularInline):
        model = MetadataColumn
        extra = 1
        show_change_link = True
        
    inlines = [MetadataColumnInline]

@admin.register(MetadataColumn)
class MetadataColumnAdmin(admin.ModelAdmin):
    list_display = ('metadata', 'column_name', 'type', 'is_required', 'is_active')
    list_filter = ('is_required', 'is_active', 'metadata')
    search_fields = ('column_name', 'metadata__primary_key')
    
    class MetadataLocalizationInline(admin.TabularInline):
        model = MetadataLocalization
        extra = 1
        
    inlines = [MetadataLocalizationInline]

@admin.register(MetadataLocalization)
class MetadataLocalizationAdmin(admin.ModelAdmin):
    list_display = ('metadata_column', 'language', 'title')
    list_filter = ('language', 'metadata_column')
    search_fields = ('title', 'metadata_column__column_name')

@admin.register(Filter)
class FilterAdmin(admin.ModelAdmin):
    list_display = ('filter_name', 'type', 'is_active')
    search_fields = ('filter_name', )
    list_filter = ('is_active', 'type')
    
    class FilterItemInline(admin.TabularInline):
        model = FilterItem
        extra = 1
    
    inlines = [FilterItemInline]

@admin.register(FilterItem)
class FilterItemAdmin(admin.ModelAdmin):
    list_display = ('filter', 'item_key', 'is_active')
    search_fields = ('item_key', )
    list_filter = ('is_active', 'filter')
    
    class FilterItemLocalizationInline(admin.TabularInline):
        model = FilterItemLocalization
        extra = 1
    
    inlines = [FilterItemLocalizationInline]

@admin.register(FilterLocalization)
class FilterLocalizationAdmin(admin.ModelAdmin):
    list_display = ('filter', 'language', 'title')
    list_filter = ('language', 'filter')
    search_fields = ('title', 'filter__filter_name')

@admin.register(FilterItemLocalization)
class FilterItemLocalizationAdmin(admin.ModelAdmin):
    list_display = ('filter_item', 'language', 'item_value')
    list_filter = ('language', 'filter_item')
    search_fields = ('item_value', 'filter_item__item_key')
