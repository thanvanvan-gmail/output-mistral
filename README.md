# output-mistral

## IFC model

- `ifc/CBN-PCC-ZZ-ST-M3-00001_IFC4X3.ifc` — Mô hình IFC4X3 "Cống kiểm soát triều rách Bình Nhãm"
  - 1.130 cấu kiện (IfcFooting / IfcBeam / IfcColumn / IfcWall / IfcSlab / IfcBuildingElementProxy)
  - Hình học `IfcTriangulatedFaceSet` (Tessellation), đơn vị mét
  - Mỗi cấu kiện có `Pset_CBNElement` (Mark, ElementId, Category, Family, Type, Material, Volume, Length, Comment)
  - Mở được bằng BIMvision, Solibri hoặc trình xem IFC bất kỳ

## Demo IFC đơn giản

- `demo/demo_1cot.ifc` — IFC4 với 01 cột `IfcColumn` (400x400x3000mm), hình học `IfcFacetedBrep`, có `IfcLocalPlacement` và `Pset_ColumnCommon`
