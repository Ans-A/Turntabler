bl_info = {
    "name": "Preview Render Automation",
    "author": "Al Ansari",
    "version": (0, 0, 2),
    "blender": (4.1),
    "location": "View3D > Sidebar > Preview Render",
    "description": "Automate preview renders with customizable settings.",
    "category": "Render",
}

import bpy
import os
import glob
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
)
import math


default_output_path = os.path.join('D:', 'projects', 'dailies')


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
    render_engine: EnumProperty(
        name="Render Engine",
        items=[
            ('BLENDER_WORKBENCH', "Workbench", ""),
            ('BLENDER_EEVEE_NEXT', "Eevee", ""),
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
    )

    rotation_degrees: FloatProperty(
        name="Object Rotation Degrees",
        default=720.0,
    )

    hdri_rotation_degrees: FloatProperty(
        name="HDRI Rotation Degrees",
        default=720.0,
    )

    output_path: StringProperty(
        name="Output Path",
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
    )

    resolution_y: IntProperty(
        name="Resolution Y",
        default=1080,
        min=1,
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
        layout.prop(settings, "resolution_percentage")
        layout.prop(settings, "custom_resolution")
        if settings.custom_resolution:
            layout.prop(settings, "resolution_x")
            layout.prop(settings, "resolution_y")
        layout.prop(settings, "frame_count")
        layout.prop(settings, "rotation_degrees")
        layout.prop(settings, "hdri_rotation_degrees")

        layout.label(text="HDRI Settings:")
        layout.prop(settings, "hdri_directory")
        layout.prop(settings, "hdri_file")

        layout.prop(settings, "output_path")
        layout.prop(settings, "file_format")
        layout.prop(settings, "wireframe_toggle")
        layout.prop(settings, "use_active_camera")
        if not settings.use_active_camera:
            layout.prop(settings, "camera_object")
        layout.prop(settings, "material_override")
        if settings.material_override:
            layout.prop(settings, "override_material")
        layout.prop(settings, "lighting_preset")
        layout.operator("preview_render.start", text="Render")


class PREVIEWRENDER_OT_start(bpy.types.Operator):
    bl_idname = "preview_render.start"
    bl_label = "Start Preview Render"

    def execute(self, context):
        settings = context.scene.preview_render_settings
        scene = context.scene
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        empty = bpy.data.objects.new("Preview_Empty", None)
        empty.location = (0, 0, 0)

        collection_name = "Preview_Collection"
        if collection_name not in bpy.data.collections:
            preview_collection = bpy.data.collections.new(collection_name)
            scene.collection.children.link(preview_collection)
        else:
            preview_collection = bpy.data.collections[collection_name]

        preview_collection.objects.link(empty)

        for obj in selected_objects:
            obj.parent = empty

        empty.rotation_euler = (0, 0, 0)
        empty.keyframe_insert(data_path="rotation_euler", frame=1)
        empty.rotation_euler = (
            0,
            0,
            math.radians(settings.rotation_degrees),
        )
        empty.keyframe_insert(data_path="rotation_euler", frame=settings.frame_count)

        scene.render.engine = settings.render_engine
        scene.render.resolution_percentage = int(settings.resolution_percentage)
        if settings.custom_resolution:
            scene.render.resolution_x = settings.resolution_x
            scene.render.resolution_y = settings.resolution_y
        scene.frame_start = 1
        scene.frame_end = settings.frame_count

        output_dir = bpy.path.abspath(settings.output_path)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        scene.render.filepath = os.path.join(output_dir, "")


        if settings.file_format == 'FFMPEG':
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.format = 'MPEG4'
        else:
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
        else:
            for obj in selected_objects:
                obj.display_type = 'TEXTURED'


        if settings.render_engine == 'BLENDER_WORKBENCH':
            pass

        elif settings.render_engine in {'BLENDER_EEVEE_NEXT', 'CYCLES'}:
            self.setup_hdri_world(context, settings)
            self.animate_hdri_rotation(context, settings)

            if settings.render_engine == 'BLENDER_EEVEE_NEXT':

                scene.eevee.use_gtao = True


        self.apply_lighting_preset(context, settings.lighting_preset)


        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

        return {'FINISHED'}

    def setup_hdri_world(self, context, settings):
        hdri_path = settings.hdri_file

        if not hdri_path or hdri_path == 'NONE':
            self.report({'WARNING'}, "No HDRI file selected.")
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

        tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
        mapping_node = nodes.new(type='ShaderNodeMapping')
        env_tex_node = nodes.new(type='ShaderNodeTexEnvironment')
        background_node = nodes.new(type='ShaderNodeBackground')
        output_node = nodes.new(type='ShaderNodeOutputWorld')


        try:
            env_tex_node.image = bpy.data.images.load(hdri_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load HDRI image from {hdri_path}")
            return

        links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
        links.new(mapping_node.outputs['Vector'], env_tex_node.inputs['Vector'])
        links.new(env_tex_node.outputs['Color'], background_node.inputs['Color'])
        links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

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

    def apply_lighting_preset(self, context, preset):
        if preset == 'STUDIO':

            for obj in list(bpy.data.objects):
                if obj.type == 'LIGHT':
                    bpy.data.objects.remove(obj, do_unlink=True)

            key_light_data = bpy.data.lights.new(name="Key Light", type='AREA')
            key_light = bpy.data.objects.new(name="Key Light", object_data=key_light_data)
            context.collection.objects.link(key_light)
            key_light.location = (5, -5, 5)
            key_light.rotation_euler = (math.radians(45), 0, math.radians(45))
            key_light_data.energy = 1000

            fill_light_data = bpy.data.lights.new(name="Fill Light", type='AREA')
            fill_light = bpy.data.objects.new(name="Fill Light", object_data=fill_light_data)
            context.collection.objects.link(fill_light)
            fill_light.location = (-5, -5, 5)
            fill_light.rotation_euler = (math.radians(45), 0, math.radians(-45))
            fill_light_data.energy = 500

        elif preset == 'SUNSET':

            for obj in list(bpy.data.objects):
                if obj.type == 'LIGHT':
                    bpy.data.objects.remove(obj, do_unlink=True)

            sun_light_data = bpy.data.lights.new(name="Sun Light", type='SUN')
            sun_light = bpy.data.objects.new(name="Sun Light", object_data=sun_light_data)
            context.collection.objects.link(sun_light)
            sun_light.rotation_euler = (math.radians(120), 0, math.radians(45))
            sun_light_data.energy = 5
            sun_light_data.color = (1.0, 0.5, 0.0) 



classes = (
    PreviewRenderSettings,
    PREVIEWRENDER_PT_panel,
    PREVIEWRENDER_OT_start,
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