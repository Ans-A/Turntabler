bl_info = {
    "name": "Preview Render Automation",
    "author": "Al Ansari",
    "version": (0, 2, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Preview Render",
    "description": "Automate preview renders with customizable settings.",
    "category": "Render",
}



import bpy
import os
import glob
import tempfile
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
)
import math

default_output_path = os.path.join(tempfile.gettempdir(), 'blender_turntables')

PREVIEW_BACKUP = {}

def get_hdri_files(self, context):
    scn = context.scene
    settings = scn.preview_render_settings

    hdri_dir = bpy.path.abspath(settings.hdri_directory)
    items = []

    if os.path.isdir(hdri_dir):
        hdri_paths = glob.glob(os.path.join(hdri_dir, '*.hdr')) + glob.glob(os.path.join(hdri_dir, '*.exr'))
        for idx, hdri_path in enumerate(hdri_paths):
            hdri_name = os.path.basename(hdri_path)
            items.append((hdri_path, hdri_name, "", idx))
    else:
        items.append(('NONE', 'No HDRIs Found', '', 0))

    if not items:
        items.append(('NONE', 'No HDRIs Found', '', 0))

    return items



class PreviewRenderSettings(bpy.types.PropertyGroup):
    def get_eevee_id():
        if bpy.app.version >= (5, 0, 0):
            return 'BLENDER_EEVEE' 
        elif bpy.app.version >= (4, 2, 0):
            return 'BLENDER_EEVEE_NEXT'
        else:
            return 'BLENDER_EEVEE'

    render_engine: EnumProperty(
        name="Render Engine",
        items=[
            ('BLENDER_WORKBENCH', "Workbench", ""),
            (get_eevee_id(), "Eevee", ""),
            ('CYCLES', "Cycles", ""),
        ],
        default='BLENDER_WORKBENCH',
    )

    resolution_percentage: EnumProperty(
        name="Resolution",
        items=[
            ('100', "100%", ""),
            ('75', "75%", ""),
            ('50', "50%", ""),
            ('40', "40%", ""),
            ('30', "30%", ""),
        ],
        default='100',
    )

    frame_count: IntProperty(
        name="Frame Count",
        default=200,
        min=1,
        max=10000,
        description="Number of frames to render"
    )

    rotation_degrees: FloatProperty(
        name="Object Rotation Degrees",
        default=720.0,
        min=-3600.0,
        max=3600.0,
    )

    hdri_rotation_degrees: FloatProperty(
        name="HDRI Rotation Degrees",
        default=720.0,
        min=-3600.0,
        max=3600.0,
    )

    auto_save_path: BoolProperty(
        name="Auto-Save to Project Folder",
        default=True,
        description="Automatically create a 'Preview_Renders' folder next to the .blend file."
    )

    output_path: StringProperty(
        name="Custom Output Path",
        default=default_output_path,
        subtype='DIR_PATH',
    )

    wireframe_toggle: BoolProperty(
        name="Wireframe Mode",
        default=False,
    )

    custom_resolution: BoolProperty(
        name="Custom Resolution",
        default=False,
    )

    resolution_x: IntProperty(
        name="Resolution X",
        default=1920,
        min=1,
        max=8192,
    )

    resolution_y: IntProperty(
        name="Resolution Y",
        default=1080,
        min=1,
        max=8192,
    )

    file_format: EnumProperty(
        name="File Format",
        items=[
            ('PNG', 'PNG', ''),
            ('JPEG', 'JPEG', ''),
            ('FFMPEG', 'Video', ''),
        ],
        default='PNG',
    )

    use_active_camera: BoolProperty(
        name="Use Active Camera",
        default=True,
    )

    camera_object: PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'CAMERA',
    )

    material_override: BoolProperty(
        name="Material Override",
        default=False,
    )

    override_material: PointerProperty(
        name="Override Material",
        type=bpy.types.Material,
    )

    lighting_preset: EnumProperty(
        name="Lighting Preset",
        items=[
            ('NONE', 'None', ''),
            ('STUDIO', 'Studio', ''),
            ('SUNSET', 'Sunset', ''),
        ],
        default='NONE',
    )

    hdri_directory: StringProperty(
        name="HDRI Directory",
        default="",
        subtype='DIR_PATH',
    )

    hdri_file: EnumProperty(
        name="HDRI File",
        items=get_hdri_files,
    )


class PREVIEWRENDER_PT_panel(bpy.types.Panel):
    bl_label = "Preview Render"
    bl_idname = "PREVIEWRENDER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Preview Render'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.preview_render_settings

        layout.prop(settings, "render_engine")
        
        if settings.render_engine == 'BLENDER_WORKBENCH':
            display = context.scene.display
            shading = display.shading
            
            box = layout.box()
            box.label(text="Workbench Settings", icon='BRUSH_DATA')
            
            col = box.column(align=True)
            col.label(text="Sampling")
            col.prop(display, "render_aa", text="Render Samples")
            col.prop(display, "viewport_aa", text="Viewport AA")
            
            box.separator()
            
            box.label(text="Lighting")
            row = box.row()
            row.prop(shading, "light", expand=True)
            
            if shading.light == 'STUDIO':
                box.template_icon_view(shading, "studio_light", scale=4.0)
                box.prop(shading, "studiolight_rotate_z", text="Rotation")
            elif shading.light == 'MATCAP':
                box.template_icon_view(shading, "studio_light", scale=4.0)
            
            layout.separator()

        layout.prop(settings, "resolution_percentage")
        layout.prop(settings, "custom_resolution")
        if settings.custom_resolution:
            layout.prop(settings, "resolution_x")
            layout.prop(settings, "resolution_y")
        layout.prop(settings, "frame_count")
        layout.prop(settings, "rotation_degrees")
        
        if settings.render_engine != 'BLENDER_WORKBENCH':
            layout.prop(settings, "hdri_rotation_degrees")
            layout.label(text="HDRI Settings:")
            layout.prop(settings, "hdri_directory")
            layout.prop(settings, "hdri_file")

        layout.separator()
        layout.label(text="Output:")
        layout.prop(settings, "auto_save_path")
        
        if not settings.auto_save_path:
            layout.prop(settings, "output_path")
            
        layout.prop(settings, "file_format")
        
        layout.separator()
        layout.prop(settings, "wireframe_toggle")
        layout.prop(settings, "use_active_camera")
        if not settings.use_active_camera:
            layout.prop(settings, "camera_object")
        layout.prop(settings, "material_override")
        if settings.material_override:
            layout.prop(settings, "override_material")
        
        if settings.render_engine != 'BLENDER_WORKBENCH':
            layout.prop(settings, "lighting_preset")
        
        layout.separator()
        layout.operator("preview_render.start", text="Render", icon='RENDER_ANIMATION')
        layout.operator("preview_render.cleanup", text="Cleanup Preview Objects", icon='TRASH')


class SceneStateBackup:
    def __init__(self, scene):
        self.scene = scene
        self.render_engine = scene.render.engine
        self.resolution_percentage = scene.render.resolution_percentage
        self.resolution_x = scene.render.resolution_x
        self.resolution_y = scene.render.resolution_y
        self.frame_start = scene.frame_start
        self.frame_end = scene.frame_end
        self.filepath = scene.render.filepath
        self.file_format = scene.render.image_settings.file_format
        
        self.media_type = getattr(scene.render.image_settings, 'media_type', None)
        
        self.camera = scene.camera
        self.ffmpeg_format = None
        if hasattr(scene.render, 'ffmpeg'):
             self.ffmpeg_format = scene.render.ffmpeg.format
        
    def restore(self):
        self.scene.render.engine = self.render_engine
        self.scene.render.resolution_percentage = self.resolution_percentage
        self.scene.render.resolution_x = self.resolution_x
        self.scene.render.resolution_y = self.resolution_y
        self.scene.frame_start = self.frame_start
        self.scene.frame_end = self.frame_end
        self.scene.render.filepath = self.filepath
        
        if self.media_type:
             self.scene.render.image_settings.media_type = self.media_type
        
        self.scene.render.image_settings.file_format = self.file_format
        self.scene.camera = self.camera
        if self.ffmpeg_format:
            self.scene.render.ffmpeg.format = self.ffmpeg_format


class PREVIEWRENDER_OT_start(bpy.types.Operator):
    bl_idname = "preview_render.start"
    bl_label = "Start Preview Render"
    bl_description = "Start automated preview render with current settings"

    def execute(self, context):
        global PREVIEW_BACKUP
        settings = context.scene.preview_render_settings
        scene = context.scene
        
        selected_object_names = [obj.name for obj in context.selected_objects]

        if not selected_object_names:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        self.cleanup_existing_preview_objects(context)

        selected_objects = []
        for name in selected_object_names:
            if name in bpy.data.objects:
                selected_objects.append(bpy.data.objects[name])
        
        if not selected_objects:
             self.report({'ERROR'}, "Selection lost during cleanup.")
             return {'CANCELLED'}

        scene_backup = SceneStateBackup(scene)
        
        orig_parents = {}
        orig_materials = {}
        orig_display_types = {}
        
        for obj in selected_objects:
            orig_parents[obj.name] = obj.parent
            orig_display_types[obj.name] = obj.display_type
            if obj.type == 'MESH':
                orig_materials[obj.name] = [slot.material for slot in obj.material_slots]

        original_visibility = {}
        view_layer = context.view_layer

        try:
            render_filepath = ""
            if settings.auto_save_path:
                if bpy.data.is_saved:
                    base_path = os.path.dirname(bpy.data.filepath)
                else:
                    base_path = tempfile.gettempdir()
                    self.report({'WARNING'}, "File not saved. Saving to temporary directory.")

                preview_dir = os.path.join(base_path, "Preview_Renders")
                if not os.path.exists(preview_dir):
                    os.makedirs(preview_dir)

                existing_folders = [d for d in os.listdir(preview_dir) if d.startswith("render_")]
                
                max_version = 0
                for folder in existing_folders:
                    try:
                        version = int(folder.split("_")[-1])
                        if version > max_version:
                            max_version = version
                    except ValueError:
                        pass
                
                new_version = max_version + 1
                new_folder_name = f"render_{new_version:03d}"
                output_dir = os.path.join(preview_dir, new_folder_name)
                os.makedirs(output_dir, exist_ok=True)
                
                if settings.file_format == 'FFMPEG':
                    render_filepath = os.path.join(output_dir, "preview.mp4")
                else:
                    render_filepath = os.path.join(output_dir, "frame_")
            else:
                output_dir = bpy.path.abspath(settings.output_path)
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)
                render_filepath = os.path.join(output_dir, "")

            scene.render.filepath = render_filepath

            empty = bpy.data.objects.new("Preview_Empty", None)
            empty.location = (0, 0, 0)

            collection_name = "Preview_Collection"
            preview_collection = bpy.data.collections.new(collection_name)
            scene.collection.children.link(preview_collection)

            preview_collection.objects.link(empty)

            for obj in selected_objects:
                obj.parent = empty
                if obj.name not in preview_collection.objects:
                    preview_collection.objects.link(obj)

            for layer_col in view_layer.layer_collection.children:
                original_visibility[layer_col.name] = layer_col.exclude
                if layer_col.collection == preview_collection:
                    layer_col.exclude = False 
                else:
                    layer_col.exclude = True

            empty.rotation_euler = (0, 0, 0)
            empty.keyframe_insert(data_path="rotation_euler", frame=1)
            empty.rotation_euler = (0, 0, math.radians(settings.rotation_degrees))
            empty.keyframe_insert(data_path="rotation_euler", frame=settings.frame_count)

            if empty.animation_data and empty.animation_data.action:
                self.set_linear_interpolation(empty.animation_data.action)

            scene.render.engine = settings.render_engine
            scene.render.resolution_percentage = int(settings.resolution_percentage)
            if settings.custom_resolution:
                scene.render.resolution_x = settings.resolution_x
                scene.render.resolution_y = settings.resolution_y
            scene.frame_start = 1
            scene.frame_end = settings.frame_count

            if settings.file_format == 'FFMPEG':
                if hasattr(scene.render.image_settings, 'media_type'):
                    scene.render.image_settings.media_type = 'VIDEO'
                try:
                    scene.render.image_settings.file_format = 'FFMPEG'
                except (TypeError, ValueError):
                    pass
                scene.render.ffmpeg.format = 'MPEG4'
            else:
                if hasattr(scene.render.image_settings, 'media_type'):
                    scene.render.image_settings.media_type = 'IMAGE'
                scene.render.image_settings.file_format = settings.file_format

            if not settings.use_active_camera and settings.camera_object:
                scene.camera = settings.camera_object

            if settings.material_override and settings.override_material:
                for obj in selected_objects:
                    if obj.type == 'MESH':
                        for slot in obj.material_slots:
                            slot.material = settings.override_material

            if settings.wireframe_toggle:
                for obj in selected_objects:
                    obj.display_type = 'WIRE'

            eevee_ids = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}
            if settings.render_engine in eevee_ids or settings.render_engine == 'CYCLES':
                self.setup_hdri_world(context, settings)
                self.animate_hdri_rotation(context, settings)
                
                if settings.render_engine in eevee_ids and hasattr(scene, 'eevee'):
                     if hasattr(scene.eevee, 'use_gtao'):
                        scene.eevee.use_gtao = True

            if settings.render_engine != 'BLENDER_WORKBENCH':
                self.apply_lighting_preset(context, settings.lighting_preset, preview_collection, selected_objects)

            self.report({'INFO'}, f"Starting render to: {render_filepath}")
            bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
            
        except Exception as e:
            self.report({'ERROR'}, f"Render setup failed: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup_and_restore(context, scene_backup, orig_parents, 
                                   orig_materials, orig_display_types, selected_objects, original_visibility)
            return {'CANCELLED'}

        PREVIEW_BACKUP = {
            'parents': orig_parents,
            'materials': orig_materials,
            'display_types': orig_display_types,
            'scene_backup': scene_backup,
            'visibility': original_visibility
        }
        
        return {'FINISHED'}

    def cleanup_existing_preview_objects(self, context):
        for obj in bpy.data.objects:
            if obj.name.startswith("Preview_Empty"):
                for child in obj.children:
                    child.parent = None
        
        # TODO: maybe add confirmation dialog here?
        for obj in list(bpy.data.objects):
            if obj.name.startswith("Preview_Empty") or (obj.type == 'LIGHT' and obj.name.startswith("Preview_")):
                 bpy.data.objects.remove(obj, do_unlink=True)

        col = bpy.data.collections.get("Preview_Collection")
        if col:
            for obj in list(col.objects):
                col.objects.unlink(obj)
                if len(obj.users_collection) == 0:
                    context.scene.collection.objects.link(obj)
            
            bpy.data.collections.remove(col)

    def set_linear_interpolation(self, action):
        if not action:
            return

        def process_fcurves(fcurves):
            for fc in fcurves:
                for kf in fc.keyframe_points:
                    kf.interpolation = 'LINEAR'

        if hasattr(action, "fcurves"):
            process_fcurves(action.fcurves)
            
        elif hasattr(action, "layers"):
            for layer in action.layers:
                if hasattr(layer, "strips"):
                    for strip in layer.strips:
                        if hasattr(strip, "fcurves"):
                            process_fcurves(strip.fcurves)

    def setup_hdri_world(self, context, settings):
        hdri_path = settings.hdri_file

        if not hdri_path or hdri_path == 'NONE':
            return

        if not os.path.isfile(hdri_path):
            self.report({'ERROR'}, f"HDRI file not found: {hdri_path}")
            return

        world = context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            context.scene.world = world

        if not world.use_nodes:
            world.use_nodes = True

        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()

        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        env_tex = nodes.new('ShaderNodeTexEnvironment')
        background = nodes.new('ShaderNodeBackground')
        output = nodes.new('ShaderNodeOutputWorld')

        try:
            env_tex.image = bpy.data.images.load(hdri_path, check_existing=True)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load HDRI: {e}")
            return

        # connect everything up
        links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
        links.new(env_tex.outputs['Color'], background.inputs['Color'])
        links.new(background.outputs['Background'], output.inputs['Surface'])

    def animate_hdri_rotation(self, context, settings):
        world = context.scene.world
        if not world or not world.node_tree:
            return

        nodes = world.node_tree.nodes
        mapping_node = None
        for node in nodes:
            if node.type == 'MAPPING':
                mapping_node = node
                break

        if mapping_node:
            rotation_input = mapping_node.inputs['Rotation']
            rotation_input.default_value[2] = 0
            rotation_input.keyframe_insert(data_path="default_value", index=2, frame=1)
            rotation_input.default_value[2] = math.radians(settings.hdri_rotation_degrees)
            rotation_input.keyframe_insert(data_path="default_value", index=2, frame=settings.frame_count)
            
            # linear interp looks better
            if world.node_tree.animation_data and world.node_tree.animation_data.action:
                 self.set_linear_interpolation(world.node_tree.animation_data.action)

    def apply_lighting_preset(self, context, preset, preview_collection, selected_objects):
        if preset == 'NONE':
            return
            
        for obj in list(preview_collection.objects):
            if obj.type == 'LIGHT' and obj not in selected_objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        if preset == 'STUDIO':
            key_light_data = bpy.data.lights.new(name="Preview_Key_Light", type='AREA')
            key_light = bpy.data.objects.new(name="Preview_Key_Light", object_data=key_light_data)
            preview_collection.objects.link(key_light)
            key_light.location = (5, -5, 5)
            key_light.rotation_euler = (math.radians(45), 0, math.radians(45))
            key_light_data.energy = 1000

            fill_light_data = bpy.data.lights.new(name='Preview_Fill_Light', type='AREA')
            fill_light = bpy.data.objects.new(name='Preview_Fill_Light', object_data=fill_light_data)
            preview_collection.objects.link(fill_light)
            fill_light.location = (-5, -5, 5)
            fill_light.rotation_euler = (math.radians(45), 0, math.radians(-45))
            fill_light_data.energy = 500

        elif preset == 'SUNSET':
            sun_light_data = bpy.data.lights.new(name="Preview_Sun_Light", type='SUN')
            sun_light = bpy.data.objects.new(name="Preview_Sun_Light", object_data=sun_light_data)
            preview_collection.objects.link(sun_light)
            sun_light.rotation_euler = (math.radians(120), 0, math.radians(45))
            sun_light_data.energy = 5
            sun_light_data.color = (1.0, 0.5, 0.0)

    def cleanup_and_restore(self, context, scene_backup, orig_parents, 
                           orig_materials, orig_display_types, selected_objects, original_visibility):
        if scene_backup:
            scene_backup.restore()
        
        view_layer = context.view_layer
        for layer_col in view_layer.layer_collection.children:
            if layer_col.name in original_visibility:
                layer_col.exclude = original_visibility[layer_col.name]

        valid_objects = [obj for obj in selected_objects if obj and obj.name in bpy.data.objects]

        for obj in valid_objects:
            if obj.name in orig_parents:
                try:
                    obj.parent = orig_parents[obj.name]
                except ReferenceError:
                    pass
                
        for obj in valid_objects:
            if obj.type == 'MESH' and obj.name in orig_materials:
                for slot, mat in zip(obj.material_slots, orig_materials[obj.name]):
                    slot.material = mat
                    
        for obj in valid_objects:
            if obj.name in orig_display_types:
                obj.display_type = orig_display_types[obj.name]


class PREVIEWRENDER_OT_cleanup(bpy.types.Operator):
    bl_idname = "preview_render.cleanup"
    bl_label = "Cleanup Preview Objects"
    bl_description = "Remove preview objects and restore original scene state"

    def execute(self, context):
        global PREVIEW_BACKUP
        
        orig_parents = PREVIEW_BACKUP.get('parents', {})
        orig_materials = PREVIEW_BACKUP.get('materials', {})
        orig_display_types = PREVIEW_BACKUP.get('display_types', {})
        original_visibility = PREVIEW_BACKUP.get('visibility', {})
        scene_backup = PREVIEW_BACKUP.get('scene_backup', None)
        
        if scene_backup:
            scene_backup.restore()

        view_layer = context.view_layer
        for layer_col in view_layer.layer_collection.children:
            if layer_col.name in original_visibility:
                layer_col.exclude = original_visibility[layer_col.name]

        for obj_name, parent in orig_parents.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                try:
                    obj.parent = parent
                except ReferenceError:
                    pass
        
        for obj_name, materials in orig_materials.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                if obj.type == 'MESH':
                    for slot, mat in zip(obj.material_slots, materials):
                        slot.material = mat
        
        for obj_name, display_type in orig_display_types.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                obj.display_type = display_type
        
        col = bpy.data.collections.get("Preview_Collection")
        
        for obj in list(bpy.data.objects):
            if obj.name.startswith("Preview_Empty") or (obj.type == 'LIGHT' and obj.name.startswith("Preview_")):
                 bpy.data.objects.remove(obj, do_unlink=True)
        
        if col:
            for obj in list(col.objects):
                col.objects.unlink(obj)
                if len(obj.users_collection) == 0:
                    context.scene.collection.objects.link(obj)
            bpy.data.collections.remove(col)
            
        PREVIEW_BACKUP = {}
        self.report({'INFO'}, "Preview objects cleaned up successfully")
        return {'FINISHED'}


classes = (
    PreviewRenderSettings,
    PREVIEWRENDER_PT_panel,
    PREVIEWRENDER_OT_start,
    PREVIEWRENDER_OT_cleanup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.preview_render_settings = PointerProperty(type=PreviewRenderSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.preview_render_settings


if __name__ == "__main__":
    register()