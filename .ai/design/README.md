# .ai/design — System Design Documents

## Purpose

Thư mục chứa toàn bộ tài liệu thiết kế hệ thống Student-Document-OCR: từ yêu cầu nghiệp vụ,
SRS, use case đến thiết kế database, API, UI và bảo mật.

## Scope

14 tài liệu thiết kế chia theo 4 nhóm:

| Nhóm | Files |
|------|-------|
| **Yêu cầu (Requirements)** | SRS.md, BusinessRequirement.md, FunctionalRequirement.md, NonFunctionalRequirement.md |
| **Kiến trúc (Architecture)** | Architecture.md, DeploymentDiagram.md |
| **Mô hình hóa (Modeling)** | UseCase.md, ERD.md, SequenceDiagram.md, ActivityDiagram.md |
| **Chi tiết (Detail Design)** | Database.md, API.md, UI.md, Security.md |

## TODO

- [ ] Hoàn thiện SRS.md và xác nhận với GVHD
- [ ] Vẽ ERD bằng dbdiagram.io, export PNG và nhúng vào ERD.md
- [ ] Vẽ C4 Architecture diagram (Level 1, 2, 3)
- [ ] Vẽ Sequence Diagram cho OCR pipeline và search flow
- [ ] Hoàn thiện API.md với OpenAPI spec đầy đủ
- [ ] Review Security.md trước khi bắt đầu Phase 3

## References

- .ai/PROJECT_SPEC.md
- .ai/ARCHITECTURE.md
- .ai/DECISIONS.md
- backend/README.md
- frontend/README.md
