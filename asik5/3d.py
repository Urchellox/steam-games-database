import open3d as o3d
import numpy as np
import copy
import os

INPUT_MESH_PATH = r"C:\Users\yrami\Desktop\asik5\Porsche.obj" 
TEXTURE_PATH = r"C:\Users\yrami\Desktop\asik5\Porsche8.PNG"

def print_header(step):
    print('\n' + '='*40)
    print(f'STEP {step}')
    print('='*40)

print_header(1)
if not os.path.exists(INPUT_MESH_PATH):
    raise FileNotFoundError(f"Не найден файл меша: {INPUT_MESH_PATH}. Поместите .obj рядом со скриптом и укажите корректное имя.")

mesh = o3d.io.read_triangle_mesh(INPUT_MESH_PATH, enable_post_processing=True)
if not mesh.has_vertex_normals():
    mesh.compute_vertex_normals()

if os.path.exists(TEXTURE_PATH):
    try:
        mesh.textures = [o3d.geometry.Image(o3d.io.read_image(TEXTURE_PATH))]
    except Exception as e:
        print('Не удалось применить текстуру:', e)

print('Оригинальная модель')
o3d.visualization.draw_geometries([mesh], window_name='1. Original Mesh')

num_vertices = np.asarray(mesh.vertices).shape[0]
num_triangles = np.asarray(mesh.triangles).shape[0]
has_color = mesh.has_vertex_colors() or (len(mesh.textures) > 0 if hasattr(mesh, 'textures') else False)
has_normals = mesh.has_vertex_normals()
print(f'Количество вершин: {num_vertices}')
print(f'Количество треугольников: {num_triangles}')
print(f'Наличие цвета: {has_color}')
print(f'Наличие нормалей: {has_normals}')

print_header(2)
pcd_from_mesh = mesh.sample_points_uniformly(number_of_points=200000)
tmp_ply = '_tmp_pointcloud.ply'
o3d.io.write_point_cloud(tmp_ply, pcd_from_mesh)
pcd = o3d.io.read_point_cloud(tmp_ply)
try:
    os.remove(tmp_ply)
except Exception:
    pass

print('point cloud')
o3d.visualization.draw_geometries([pcd], window_name='2. Point Cloud')

num_pcd_vertices = np.asarray(pcd.points).shape[0]
has_pcd_color = pcd.has_colors()
print(f'Количество вершин в облаке: {num_pcd_vertices}')
print(f'Наличие цвета в облаке: {has_pcd_color}')


print_header(3)
with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug) as cm:
    mesh_poisson, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)

bbox = mesh.get_axis_aligned_bounding_box()
mesh_poisson_crop = mesh_poisson.crop(bbox)

if not mesh_poisson_crop.has_vertex_normals():
    mesh_poisson_crop.compute_vertex_normals()

print('реконструированная моделька')
o3d.visualization.draw_geometries([mesh_poisson_crop], window_name='3. Poisson Reconstructed (Cropped)')

num_poisson_vertices = np.asarray(mesh_poisson_crop.vertices).shape[0]
num_poisson_triangles = np.asarray(mesh_poisson_crop.triangles).shape[0]
has_poisson_color = mesh_poisson_crop.has_vertex_colors() or (len(mesh_poisson_crop.textures) > 0 if hasattr(mesh_poisson_crop, 'textures') else False)
print(f'Количество вершин: {num_poisson_vertices}')
print(f'Количество треугольников: {num_poisson_triangles}')
print(f'Наличие цвета: {has_poisson_color}')

print_header(4)
voxel_size = 0.05 
voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=voxel_size)

print(f'Воксели')
o3d.visualization.draw_geometries([voxel_grid], window_name='4. Voxel Grid')

num_voxels = len(voxel_grid.get_voxels())
has_voxel_color = hasattr(voxel_grid, 'colors') and (len(voxel_grid.colors) > 0)
print(f'Количество вокселей: {num_voxels}')
print(f'Наличие цвета в вокселях: {has_voxel_color}')

print("\n========================================")
print("STEP 5")
print("========================================")

bbox = mesh.get_axis_aligned_bounding_box()
center = bbox.get_center()
min_bound = bbox.get_min_bound()
max_bound = bbox.get_max_bound()

plane_width = (max_bound[1] - min_bound[1]) * 1.5
plane_height = (max_bound[2] - min_bound[2]) * 1.5
plane = o3d.geometry.TriangleMesh.create_box(width=0.001, height=plane_width, depth=plane_height)
plane.paint_uniform_color([0.2, 0.8, 1.0]) 

plane.translate([center[0] + 0.1 * (max_bound[0] - min_bound[0]), center[1] - plane_width/2, center[2] - plane_height/2])

plane.compute_vertex_normals()
vis = o3d.visualization.Visualizer()
vis.create_window(window_name="Step 5: Mesh + Plane")
vis.add_geometry(mesh)
vis.add_geometry(plane)
opt = vis.get_render_option()
opt.mesh_show_back_face = True
opt.background_color = np.asarray([0, 0, 0])
vis.run()
vis.destroy_window()

print("\n========================================")
print("STEP 6")
print("========================================")

plane_x = np.asarray(plane.vertices)[:, 0].mean()

verts = np.asarray(mesh.vertices)
tris = np.asarray(mesh.triangles)

mask = verts[:, 0] <= plane_x
valid_idx = np.nonzero(mask)[0]

keep_tris = np.all(np.isin(tris, valid_idx), axis=1)
new_verts = verts[mask]
new_tris = np.searchsorted(valid_idx, tris[keep_tris])
new_colors = np.asarray(mesh.vertex_colors)[mask] if mesh.has_vertex_colors() else None
new_normals = np.asarray(mesh.vertex_normals)[mask] if mesh.has_vertex_normals() else None

clipped_mesh = o3d.geometry.TriangleMesh()
clipped_mesh.vertices = o3d.utility.Vector3dVector(new_verts)
clipped_mesh.triangles = o3d.utility.Vector3iVector(new_tris)
if new_colors is not None:
    clipped_mesh.vertex_colors = o3d.utility.Vector3dVector(new_colors)
if new_normals is not None:
    clipped_mesh.vertex_normals = o3d.utility.Vector3dVector(new_normals)

print(f"Оставшееся количество вершин: {len(new_verts)}")
print(f"Оставшееся количество треугольников: {len(new_tris)}")
print(f"Наличие цвета после обрезки: {clipped_mesh.has_vertex_colors()}")
print(f"Наличие нормалей после обрезки: {clipped_mesh.has_vertex_normals()}")

o3d.visualization.draw_geometries([clipped_mesh], window_name="Step 6: Clipped Mesh")

print("========================================")
print("STEP 7")
print("========================================")
print("Градиент и экстремумы")

mesh_for_gradient = o3d.io.read_triangle_mesh(INPUT_MESH_PATH)
mesh_for_gradient.compute_vertex_normals()

z_values = np.asarray(mesh_for_gradient.vertices)[:, 2]
z_min, z_max = z_values.min(), z_values.max()

colors = np.zeros((len(z_values), 3))
for i, z in enumerate(z_values):
    t = (z - z_min) / (z_max - z_min)
    colors[i] = [1.0 * (1 - t) + 0.5 * t, 1.0 * (1 - t) + 0.0 * t, 0.0 * (1 - t) + 0.5 * t]

mesh_for_gradient.vertex_colors = o3d.utility.Vector3dVector(colors)

min_idx = np.argmin(z_values)
max_idx = np.argmax(z_values)
min_point = mesh_for_gradient.vertices[min_idx]
max_point = mesh_for_gradient.vertices[max_idx]

min_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.05)
min_sphere.translate(min_point)
min_sphere.paint_uniform_color([1, 0, 0])

max_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.05)
max_sphere.translate(max_point)
max_sphere.paint_uniform_color([0, 1, 0])

print("Экстремумы по оси Z:")
print(f"Мин (z): индекс {min_idx}, координаты {min_point}")
print(f"Макс (z): индекс {max_idx}, координаты {max_point}")

o3d.visualization.draw_geometries([mesh_for_gradient, min_sphere, max_sphere])