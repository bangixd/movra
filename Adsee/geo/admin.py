from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from .models import Province, City, Neighborhood, SuggestedRoute, DriverLocation


@admin.register(Province)
class ProvinceAdmin(geoadmin.GISModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(City)
class CityAdmin(geoadmin.GISModelAdmin):
    list_display = ['name', 'province', 'center']
    list_filter = ['province']
    search_fields = ['name', 'province__name']


@admin.register(Neighborhood)
class NeighborhoodAdmin(geoadmin.GISModelAdmin):
    list_display = ['name', 'city', 'radius_meter']
    list_filter = ['city__province', 'city']
    search_fields = ['name', 'city__name']


@admin.register(SuggestedRoute)
class SuggestedRouteAdmin(geoadmin.GISModelAdmin):
    list_display = ['name', 'city']
    list_filter = ['city']
    search_fields = ['name']


@admin.register(DriverLocation)
class DriverLocationAdmin(geoadmin.GISModelAdmin):
    list_display = ['driver', 'trip', 'point', 'timestamp']
    list_filter = ['trip', 'timestamp']
    search_fields = ['driver__email']
    readonly_fields = ['timestamp']

# Register your models here.
