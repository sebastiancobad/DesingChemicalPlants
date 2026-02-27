# ChemScale — Software Architecture & Functional Roadmap

**Version:** 1.0.0-DRAFT
**Date:** 2026-02-27
**Author:** Lead Architect / Senior Process Engineering
**Status:** Stakeholder Review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Tech Stack & High-Level Architecture](#2-tech-stack--high-level-architecture)
3. [Core System Foundations](#3-core-system-foundations)
4. [The Calculation Pipeline](#4-the-calculation-pipeline)
5. [Functional Engineering Modules](#5-functional-engineering-modules)
6. [Phased Development Roadmap](#6-phased-development-roadmap)
7. [Proof of Concept — Deep Dive](#7-proof-of-concept--deep-dive)
8. [Cross-Cutting Concerns](#8-cross-cutting-concerns)
9. [Appendices](#9-appendices)

---

## 1. Executive Summary

ChemScale is a cloud-native, end-to-end Chemical Engineering Design and Sizing
platform. It replaces fragmented spreadsheet workflows with a unified system
where thermodynamic calculations, equipment sizing, safety analysis, and
economic evaluation share a single source of truth.

**Key differentiators:**

- A first-principles Thermodynamic & Physical Property Engine powers every
  module — no hard-coded correlations that silently diverge.
- Every calculation traces back to a versioned industry standard (ASME, API,
  PIP, ISA, TEMA) with clause-level references.
- The architecture separates the *calculation kernel* (Python, deterministic,
  unit-testable) from the *presentation layer* (React), enabling headless
  batch runs, CI regression suites, and third-party integrations via REST/gRPC.

---

## 2. Tech Stack & High-Level Architecture

### 2.1 Technology Selections

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18 + TypeScript, Vite, TailwindCSS | Component reuse, strong typing for engineering UIs, fast HMR |
| **Charting / Plots** | Plotly.js (interactive), D3.js (custom P&ID canvas) | Plotly handles phase envelopes, pump curves; D3 handles symbol-level P&ID drafting |
| **State Management** | Zustand + React Query | Lightweight; React Query caches server-computed results |
| **Backend API** | Python 3.12, FastAPI (REST + WebSocket) | Async I/O, automatic OpenAPI docs, Pydantic validation native |
| **Calculation Kernel** | Python (NumPy, SciPy, CoolProp, Thermo) | NumPy/SciPy for linear algebra & root finding; CoolProp/Thermo for EOS |
| **Task Queue** | Celery + Redis | Long-running distillation or rating calculations offloaded to workers |
| **Primary Database** | PostgreSQL 16 | ACID for component properties, project data, audit trails |
| **Document Store** | MongoDB (optional) | Flexible storage for HAZOP templates, case study narratives |
| **Cache** | Redis | Session cache, calculation memoization, pub/sub for progress |
| **Search** | Meilisearch | Full-text search over component database, standards references |
| **Auth** | Keycloak (OIDC) or Auth0 | Enterprise SSO, RBAC for reviewer/approver workflows |
| **CI/CD** | GitHub Actions → Docker → Kubernetes (EKS/GKE) | Reproducible builds, horizontal pod autoscaling for calc workers |
| **Object Storage** | AWS S3 / MinIO | Datasheet PDFs, P&ID exports, project archives |
| **Monitoring** | Prometheus + Grafana, Sentry | Calculation latency tracking, error budgets |

### 2.2 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  React SPA  │  │ Plotly / D3  │  │  Datasheet │  │  P&ID     │ │
│  │  (Forms,    │  │  (Charts,    │  │  Generator │  │  Canvas   │ │
│  │   Dashbd)   │  │   Diagrams)  │  │  (PDF/XLSX)│  │  (SVG)    │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └─────┬─────┘ │
│         └────────────────┴────────────────┴────────────────┘       │
│                              │  HTTPS / WSS                        │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                        API GATEWAY (Kong / Traefik)                 │
│                     Rate Limiting · JWT Validation                  │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                        APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Service                           │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │   │
│  │  │ /api/v1/   │  │ WebSocket  │  │  Pydantic Schemas      │ │   │
│  │  │  REST      │  │  Progress  │  │  (Input Validation)    │ │   │
│  │  │  Endpoints │  │  Channel   │  │                        │ │   │
│  │  └─────┬──────┘  └─────┬──────┘  └────────────────────────┘ │   │
│  │        └───────────────┴──────────┐                         │   │
│  │                                   │                         │   │
│  │  ┌────────────────────────────────▼──────────────────────┐  │   │
│  │  │              CALCULATION KERNEL                       │  │   │
│  │  │  ┌───────────────────┐  ┌──────────────────────────┐  │  │   │
│  │  │  │  Thermo Engine    │  │  Engineering Modules     │  │  │   │
│  │  │  │  (EOS, Activity   │  │  (Pipe, HX, Pump,       │  │  │   │
│  │  │  │   Coefficients,   │  │   Separator, Column,    │  │  │   │
│  │  │  │   Flash, Props)   │  │   PSV, APC, Layout...)  │  │  │   │
│  │  │  └───────────────────┘  └──────────────────────────┘  │  │   │
│  │  │  ┌───────────────────┐  ┌──────────────────────────┐  │  │   │
│  │  │  │  Unit Converter   │  │  Standards Reference     │  │  │   │
│  │  │  │  (SI ↔ Imperial   │  │  (API, ASME, TEMA       │  │  │   │
│  │  │  │   ↔ Custom)       │  │   clause lookups)       │  │  │   │
│  │  │  └───────────────────┘  └──────────────────────────┘  │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                               │                                    │
│  ┌────────────────────────────▼─────────────────────────────────┐   │
│  │             Celery Workers (Heavy Calculations)              │   │
│  │    Distillation stage-by-stage · HX rating · MPC tuning     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                         DATA LAYER                                 │
│  ┌─────────────┐  ┌──────────┐  ┌───────┐  ┌──────────┐  ┌─────┐  │
│  │ PostgreSQL  │  │  Redis   │  │  S3 / │  │ MongoDB  │  │Meili│  │
│  │ (Components,│  │ (Cache,  │  │ MinIO │  │ (HAZOP   │  │srch │  │
│  │  Projects,  │  │  Queue   │  │(PDFs, │  │  Case    │  │     │  │
│  │  Audit)     │  │  Broker) │  │ SVGs) │  │  Studies)│  │     │  │
│  └─────────────┘  └──────────┘  └───────┘  └──────────┘  └─────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 2.3 Why This Stack Handles Heavy Thermodynamic Computation

1. **CPU-bound isolation:** Flash calculations and stage-by-stage distillation
   run inside Celery workers on dedicated pods. The API server never blocks.
2. **Vectorised math:** NumPy/SciPy operate on C-level arrays. A VLE flash
   with Peng-Robinson for a 20-component mixture solves in < 50 ms.
3. **Horizontal scaling:** Kubernetes HPA scales worker pods based on queue
   depth. A 100-stage distillation column rating can be sharded across workers
   via a map-reduce pattern on tray hydraulic calculations.
4. **Result caching:** Redis memoises property lookups keyed on
   `(components, T, P, model)` tuples. Identical queries return in < 1 ms.
5. **CoolProp / Thermo integration:** These open-source libraries implement
   peer-reviewed EOS with validated regression against NIST data, avoiding the
   need to re-implement Peng-Robinson from scratch while still allowing custom
   mixing rules.

---

## 3. Core System Foundations

These two subsystems are **prerequisites** for every engineering module.

### 3.1 Thermodynamic & Physical Property Engine

#### 3.1.1 Equations of State (EOS)

| Model | Use Case | Implementation |
|---|---|---|
| **Peng-Robinson (PR)** | Hydrocarbon systems, high-pressure gas processing | `thermo.eos.PR` with custom kij matrix |
| **Soave-Redlich-Kwong (SRK)** | Refinery gas systems, general vapor-phase | `thermo.eos.SRK` |
| **PR with Boston-Mathias alpha** | Supercritical fluids, hydrogen-rich systems | Custom extension of PR |
| **Lee-Kesler-Plöcker** | Enthalpy departures, heavy hydrocarbons | Custom implementation |

#### 3.1.2 Activity Coefficient Models

| Model | Use Case | Implementation |
|---|---|---|
| **NRTL** | Strongly non-ideal liquid mixtures, LLE | `thermo.nrtl.NRTL` |
| **UNIQUAC** | Polymer solutions, size-asymmetric mixtures | `thermo.uniquac.UNIQUAC` |
| **Wilson** | VLE of miscible, non-electrolyte systems | `thermo.wilson.Wilson` |
| **UNIFAC (modified Dortmund)** | Predictive — when no experimental data exists | Custom group-contribution |

#### 3.1.3 Core Property Calculations

```
PropertyEngine.calculate(components, T, P, phase, model) → PropertyResult
```

**Returned properties:**

- Density (ρ), Compressibility (Z)
- Viscosity (μ) — Lucas (gas), DIPPR correlation (liquid)
- Thermal conductivity (k)
- Heat capacity (Cp, Cv)
- Enthalpy (H), Entropy (S), Gibbs energy (G)
- Surface tension (σ)
- Fugacity coefficients (φ)
- Activity coefficients (γ)
- Vapor pressure (Antoine / Wagner)
- Flash results (VLE, VLLE) via Rachford-Rice with successive substitution
  and Newton acceleration

#### 3.1.4 Flash Algorithms

| Flash Type | Independent Vars | Algorithm |
|---|---|---|
| **PT Flash** | T, P fixed | Successive Substitution → Newton |
| **PH Flash** | P, H fixed | Nested: outer T-loop, inner PT Flash |
| **PS Flash** | P, S fixed | Nested: outer T-loop, inner PT Flash |
| **TV Flash** | T, V fixed | Pressure iteration with PT Flash |
| **Bubble Point** | T (or P), x | Converge P (or T) where Σ y_i = 1 |
| **Dew Point** | T (or P), y | Converge P (or T) where Σ x_i = 1 |

### 3.2 Component Database

#### 3.2.1 Schema (PostgreSQL)

```sql
CREATE TABLE components (
    id              SERIAL PRIMARY KEY,
    cas_number      VARCHAR(12) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    formula         VARCHAR(50),
    molecular_weight DOUBLE PRECISION NOT NULL,
    tc_k            DOUBLE PRECISION,  -- Critical temperature [K]
    pc_pa           DOUBLE PRECISION,  -- Critical pressure [Pa]
    vc_m3mol        DOUBLE PRECISION,  -- Critical volume [m³/mol]
    omega           DOUBLE PRECISION,  -- Acentric factor
    tb_k            DOUBLE PRECISION,  -- Normal boiling point [K]
    tf_k            DOUBLE PRECISION,  -- Normal freezing point [K]
    dipole_moment   DOUBLE PRECISION,  -- Debye
    std_enthalpy_formation DOUBLE PRECISION,  -- [J/mol]
    std_gibbs_formation    DOUBLE PRECISION,  -- [J/mol]
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE property_correlations (
    id              SERIAL PRIMARY KEY,
    component_id    INTEGER REFERENCES components(id),
    property_name   VARCHAR(50) NOT NULL,    -- e.g., 'vapor_pressure', 'liquid_density'
    correlation_type VARCHAR(30) NOT NULL,    -- e.g., 'DIPPR_101', 'Antoine'
    coefficients    JSONB NOT NULL,           -- {"A": ..., "B": ..., "C": ..., ...}
    t_min_k         DOUBLE PRECISION,
    t_max_k         DOUBLE PRECISION,
    units           VARCHAR(30),
    source          VARCHAR(100),            -- e.g., 'DIPPR 2023', 'NIST'
    UNIQUE(component_id, property_name, correlation_type)
);

CREATE TABLE binary_interaction_params (
    id              SERIAL PRIMARY KEY,
    component_1_id  INTEGER REFERENCES components(id),
    component_2_id  INTEGER REFERENCES components(id),
    model           VARCHAR(30) NOT NULL,    -- 'PR', 'SRK', 'NRTL', 'UNIQUAC'
    parameters      JSONB NOT NULL,          -- {"kij": 0.02} or {"tau12": ..., "tau21": ..., "alpha": 0.3}
    t_min_k         DOUBLE PRECISION,
    t_max_k         DOUBLE PRECISION,
    source          VARCHAR(100),
    UNIQUE(component_1_id, component_2_id, model)
);
```

#### 3.2.2 Seed Data Strategy

- **Phase 1:** Seed ~500 common process chemicals from open NIST/DIPPR sources.
- **Phase 2:** Allow user-contributed components with admin approval workflow.
- **Phase 3:** Integrate with commercial property databases (e.g., DECHEMA) via
  licensed API connectors.

---

## 4. The Calculation Pipeline

Every user interaction follows a deterministic, auditable pipeline:

```
  ┌──────────────┐
  │  USER INPUT  │   JSON payload from React form
  │  (validated) │   Pydantic schema enforces types, ranges, units
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────┐
  │              UNIT NORMALIZATION                       │
  │  All inputs converted to SI base units               │
  │  (K, Pa, m, kg, mol, s, W)                           │
  │  Original units preserved in metadata for output     │
  └──────────────────┬───────────────────────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────────────────────┐
  │          THERMODYNAMIC ENGINE                         │
  │                                                      │
  │  1. Resolve components from DB (CAS lookup)          │
  │  2. Select thermo model (user override or auto)      │
  │  3. Calculate mixture properties at (T, P, z)        │
  │  4. Perform flash if phase split expected             │
  │  5. Return PropertyResult object:                    │
  │     - Phase fractions, compositions                   │
  │     - ρ, μ, k, Cp, σ for each phase                 │
  │     - Fugacity / activity coefficients               │
  │                                                      │
  └──────────────────┬───────────────────────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────────────────────┐
  │          ENGINEERING MODULE                           │
  │          (e.g., Heat Exchanger Design)               │
  │                                                      │
  │  Receives: PropertyResult + module-specific inputs   │
  │                                                      │
  │  Executes: Module-specific correlations              │
  │    - Kern / Bell-Delaware for HX                     │
  │    - Darcy-Weisbach for pipe                         │
  │    - API 520 for PSV                                 │
  │    - McCabe-Thiele / Fenske-Underwood for column     │
  │                                                      │
  │  Each calculation step records:                      │
  │    - Standard reference (e.g., "TEMA 10th Ed §5.3") │
  │    - Intermediate values for audit trail             │
  │                                                      │
  └──────────────────┬───────────────────────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────────────────────┐
  │          RESULTS & OUTPUT GENERATION                  │
  │                                                      │
  │  1. Convert results back to user-preferred units     │
  │  2. Generate structured JSON response                │
  │  3. Populate datasheet template (XLSX/PDF)           │
  │  4. Store calculation record in audit table          │
  │  5. Return via REST response or WebSocket push       │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

### 4.1 Calculation Audit Record

Every calculation creates an immutable audit row:

```sql
CREATE TABLE calculation_audit (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL,
    module          VARCHAR(50) NOT NULL,       -- 'heat_exchanger', 'psv', etc.
    user_id         UUID NOT NULL,
    input_snapshot  JSONB NOT NULL,             -- exact input as received
    thermo_model    VARCHAR(30),
    output_snapshot JSONB NOT NULL,             -- full result
    standards_refs  TEXT[],                     -- ['API 660 §7.1', 'TEMA 10th §RCB-5']
    calc_version    VARCHAR(20) NOT NULL,       -- semver of the calc kernel
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Functional Engineering Modules

### Module 1 — Pipe Sizing & Hydraulics

**Standards:** ASME B31.3, API RP 14E, PIP PIPC1000
**Key calculations:**
- Darcy-Weisbach pressure drop (single-phase liquid/gas)
- Beggs-Brill or Lockhart-Martinelli (two-phase)
- Erosional velocity limit (API RP 14E): `V_e = C / √ρ_m`
- Economic pipe diameter (Peters & Timmerhaus correlation)
- Equivalent length for fittings (Crane TP-410)
- Schedule/wall thickness from ASME B36.10M

### Module 2 — Material Selection & Metallurgy

**Standards:** ASME II Part D, NACE MR0175/ISO 15156, API RP 571
**Key features:**
- Material database: Carbon steel through Hastelloy, Inconel, Titanium
- Corrosion rate calculators:
  - CO₂ (sweet): de Waard-Milliams, Norsok M-506
  - H₂S (sour): NACE MR0175 compliance checks
  - Generalized: user-input coupon data
- Mechanical property lookup at temperature (allowable stress per ASME II-D)
- Corrosion allowance → minimum required wall thickness

### Module 3 — Plant Layout & Location

**Standards:** API 2510, PIP PLC00010, NFPA 30
**Key features:**
- Inter-equipment spacing tables (API passive safety distances)
- Plot plan generator (2D SVG output with drag-and-drop)
- Wind rose overlay for flare/vent stack placement
- Access road and escape route validation

### Module 4 — Phase Separator Sizing

**Standards:** API 12J, GPSA Engineering Data Book
**Key calculations:**
- Stokes' law droplet settling velocity
- Souders-Brown K-factor for demister sizing
- Horizontal separator: L/D optimization, liquid holdup time, weir height
- Vertical separator: gas capacity, liquid surge volume
- 3-phase: water/oil interface, boot sizing
- Internals: vane pack, wire mesh demister, cyclonic inlet device

### Module 5 — Pump Selection & Sizing

**Standards:** API 610, Hydraulic Institute Standards
**Key calculations:**
- System head curve: static + friction + equipment ΔP
- NPSH available vs. NPSH required (with safety margin per API 610)
- Specific speed (Ns) → impeller type selection algorithm
- Affinity laws for speed/impeller trim changes
- Centrifugal vs. PD selection matrix
- BHP calculation with efficiency curves
- Minimum flow recirculation sizing

### Module 6 — Heat Exchanger Design

**Standards:** TEMA 10th Ed, API 660, ASME Sec VIII Div 1
*(Detailed in Proof of Concept, Section 7.1)*

### Module 7 — Rigorous Distillation Column Design

**Standards:** FRI correlations, Sulzer/Koch-Glitsch packing data
**Key calculations:**
- Shortcut: Fenske (Nmin), Underwood (Rmin), Gilliland (N vs. R)
- Rigorous: Stage-by-stage MESH equations (BP or SR method)
- Tray hydraulics: downcomer backup, weeping, flooding, jet flood
- Tray types: sieve, valve (Koch Flexitray), bubble cap
- Packed column: HETP from vendor data, capacity via Wallis correlation
- Column diameter from Fair correlation or Souders-Brown
- Condenser/reboiler duty integration with Module 6

### Module 8 — Safety Relief Valves (PSV/PRV)

**Standards:** API 520 Part I (Sizing), API 521 (Installation), ASME Sec VIII
**Key calculations:**
- Overpressure scenarios: fire case, blocked outlet, thermal expansion,
  tube rupture, control valve failure, power failure
- Gas/vapor: critical vs. subcritical flow (API 520 §4.3)
- Liquid: certified capacity with viscosity correction (API 520 §5)
- Two-phase: DIERS methodology (omega method)
- Backpressure effects: conventional vs. balanced bellows vs. pilot-operated
- Reaction force and outlet piping sizing

### Module 9 — Process Safety & Industrial Hygiene

**Standards:** OSHA PSM (29 CFR 1910.119), EPA RMP, IEC 61511
**Key features:**
- Inherent safe design checklist (MINIMIZE, SUBSTITUTE, MODERATE, SIMPLIFY)
- HAZOP worksheet templates with guidewords per IEC 61882
- Layer of Protection Analysis (LOPA) calculator
- Consequence modeling interfaces (toxic dispersion, overpressure, jet fire)
- Case study database: Bhopal (MIC release), Deepwater Horizon (blowout),
  Texas City (ISOM unit), Piper Alpha (fire/explosion), Flixborough (cyclohexane)

### Module 10 — Advanced Process Control (APC)

**Standards:** ISA-5.1, ISA-88, ISA-95
**Key features:**
- PID tuning correlations (Ziegler-Nichols, Cohen-Coon, Lambda)
- Control strategy selection matrix per unit operation:
  - Distillation: LV, DV, dual-temperature, composition control
  - Heat exchanger: bypass, valve-on-outlet, cascade
  - Reactor: cascade temperature, split-range, feedforward
- Cascade / feedforward / ratio control logic diagrams
- Model Predictive Control (MPC) scope definition templates
- Control valve sizing (ISA/IEC 60534, Cv calculation)

### Module 11 — P&ID Development

**Standards:** ISA-5.1-2022, PIP PIC001
**Key features:**
- Symbol library: ISA-standard equipment, valve, and instrument symbols (SVG)
- Auto-generated tag numbers per ISA naming convention
- Line numbering with size-material-insulation encoding
- Instrument loop diagram templates
- Export to DXF/SVG for CAD integration

### Module 12 — Economic Evaluation & Industrial Utilities

*(Detailed in Proof of Concept, Section 7.2)*

---

## 6. Phased Development Roadmap

### Phase 0 — Foundation (Weeks 1–8)

**Goal:** Establish the platform skeleton and the two core subsystems that
every module depends on.

| Deliverable | Details |
|---|---|
| **Project scaffolding** | Monorepo (Nx or Turborepo): `/backend`, `/frontend`, `/kernel`, `/shared` |
| **CI/CD pipeline** | GitHub Actions: lint, type-check, pytest, Docker build, deploy to staging |
| **Component Database** | PostgreSQL schema, seed 500 compounds, REST CRUD API |
| **Thermodynamic Engine** | PR, SRK EOS; NRTL activity model; PT/PH flash; property calculator |
| **Unit Conversion Service** | SI ↔ Imperial ↔ CGS for all engineering quantities |
| **Auth & RBAC** | Keycloak integration, project-level access control |
| **Frontend shell** | React app with routing, auth flow, component search page |

**Exit criteria:** A user can log in, search for "methane + ethane," select
Peng-Robinson, compute mixture density at 300 K / 50 bar, and see a correct
result on the UI.

---

### Phase 1 — MVP Engineering Modules (Weeks 9–20)

**Goal:** Deliver the four most commonly needed process engineering tools.

| Module | Priority Rationale |
|---|---|
| **Module 1 — Pipe Sizing** | Highest daily-use frequency; validates unit conversion + thermo integration |
| **Module 4 — Phase Separators** | Relies on flash results (tests thermo pipeline end-to-end) |
| **Module 5 — Pump Sizing** | Pairs naturally with pipe hydraulics (shared head-loss data) |
| **Module 2 — Material Selection** | Needed by pipe, separator, and all downstream modules for wall thickness |

**Additional deliverables:**
- Datasheet PDF generator (generic template engine)
- Project save/load with versioning
- Calculation audit trail

**Exit criteria:** A user can design a complete pipe run from vessel A to
vessel B, selecting materials, sizing the pipe, sizing a separator, and
selecting a pump — all within a single project workspace.

---

### Phase 2 — Advanced Design Modules (Weeks 21–36)

**Goal:** The high-value, high-complexity modules that distinguish ChemScale
from simple calculators.

| Module | Priority Rationale |
|---|---|
| **Module 6 — Heat Exchanger Design** | Most requested sizing tool; integrates tightly with thermo for zone analysis |
| **Module 7 — Distillation Column** | Flagship rigorous-calculation module; uses HX for condenser/reboiler |
| **Module 8 — PSV/PRV Sizing** | Regulatory requirement; pairs with separator, HX, and column modules |
| **Module 12 — Economic Evaluation** | Stakeholders want cost estimates as soon as equipment is sized |

**Additional deliverables:**
- WebSocket progress reporting for long calculations
- Batch calculation mode (run N cases with parameter sweeps)
- Export results to Excel with formulas intact

**Exit criteria:** A user can design a distillation column (shortcut +
rigorous), size the condenser and reboiler (heat exchangers), size the PSVs,
and generate a CAPEX estimate — all linked within one project.

---

### Phase 3 — Safety, Control & Layout (Weeks 37–48)

**Goal:** Round out the platform with safety, control, and layout capabilities.

| Module | Priority Rationale |
|---|---|
| **Module 9 — Process Safety** | HAZOP templates + case studies; lower calc complexity but high documentation value |
| **Module 10 — APC** | Control valve sizing feeds back into pipe/pump hydraulics |
| **Module 3 — Plant Layout** | Requires all equipment to be sized first; 2D interactive canvas |
| **Module 11 — P&ID Development** | Capstone module; draws on every other module's equipment data |

**Additional deliverables:**
- Collaboration features (multi-user editing, comments, approvals)
- API for third-party integrations (import from Aspen, HYSYS)
- Mobile-responsive dashboard for field reviews

**Exit criteria:** A complete plant design workflow — from thermodynamics
through equipment sizing, safety analysis, control strategy, layout, and P&ID
— can be executed within ChemScale.

---

### Roadmap Gantt Summary

```
Week:  1    4    8    12   16   20   24   28   32   36   40   44   48
       ├────┴────┤
       Phase 0: Foundation
                 ├─────────┴──────────┤
                 Phase 1: MVP (Pipe, Sep, Pump, Mat)
                                      ├──────────┴──────────┤
                                      Phase 2: HX, Column, PSV, Econ
                                                            ├──────────┤
                                                            Phase 3: Safety,
                                                            APC, Layout, P&ID
```

---

## 7. Proof of Concept — Deep Dive

### 7.1 Module 6: Heat Exchanger Design

#### 7.1.1 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/hx/quick-size` | Conceptual area estimation (LMTD, U assumed) |
| `POST` | `/api/v1/hx/rate` | Rigorous rating of an existing geometry |
| `POST` | `/api/v1/hx/design` | Iterative design to meet duty + ΔP constraints |
| `GET`  | `/api/v1/hx/tema-types` | List valid TEMA type codes with descriptions |
| `GET`  | `/api/v1/hx/materials` | Shell/tube material options with allowable stress |
| `POST` | `/api/v1/hx/datasheet` | Generate TEMA datasheet (PDF/XLSX) |

#### 7.1.2 JSON Input — Quick Sizing (`/api/v1/hx/quick-size`)

```json
{
  "project_id": "uuid",
  "tag": "E-101",
  "hx_type": "shell_and_tube",
  "tema_type": "AES",

  "hot_side": {
    "fluid": {
      "components": [
        {"cas": "7732-18-5", "name": "Water", "mole_fraction": 1.0}
      ],
      "thermo_model": "IAPWS97"
    },
    "inlet_temperature":  {"value": 150.0, "unit": "°C"},
    "outlet_temperature": {"value": 90.0,  "unit": "°C"},
    "mass_flow_rate":     {"value": 50000, "unit": "kg/h"},
    "inlet_pressure":     {"value": 500,   "unit": "kPa_g"},
    "fouling_resistance": {"value": 0.000176, "unit": "m²·K/W"},
    "max_pressure_drop":  {"value": 70, "unit": "kPa"}
  },

  "cold_side": {
    "fluid": {
      "components": [
        {"cas": "7732-18-5", "name": "Water", "mole_fraction": 1.0}
      ],
      "thermo_model": "IAPWS97"
    },
    "inlet_temperature":  {"value": 30.0, "unit": "°C"},
    "outlet_temperature": {"value": 45.0, "unit": "°C"},
    "mass_flow_rate":     null,
    "inlet_pressure":     {"value": 600, "unit": "kPa_g"},
    "fouling_resistance": {"value": 0.000176, "unit": "m²·K/W"},
    "max_pressure_drop":  {"value": 50, "unit": "kPa"}
  },

  "geometry_constraints": {
    "max_tube_length": {"value": 6.096, "unit": "m"},
    "tube_od":         {"value": 19.05, "unit": "mm"},
    "tube_pitch":      {"value": 25.4,  "unit": "mm"},
    "tube_layout":     "triangular_30",
    "baffle_cut":      0.25,
    "num_shell_passes": 1,
    "num_tube_passes":  2
  },

  "design_conditions": {
    "shell_design_pressure":  {"value": 1000, "unit": "kPa_g"},
    "tube_design_pressure":   {"value": 1000, "unit": "kPa_g"},
    "shell_design_temperature": {"value": 200, "unit": "°C"},
    "tube_design_temperature":  {"value": 200, "unit": "°C"},
    "shell_material": "SA-516-70",
    "tube_material":  "SA-179",
    "corrosion_allowance": {"value": 3.0, "unit": "mm"}
  },

  "output_units": "SI"
}
```

#### 7.1.3 JSON Output — Quick Sizing

```json
{
  "status": "success",
  "tag": "E-101",
  "tema_type": "AES",

  "thermal_results": {
    "duty":                {"value": 3488.9, "unit": "kW"},
    "lmtd":               {"value": 75.27,  "unit": "K"},
    "correction_factor_F": 0.874,
    "corrected_mtd":       {"value": 65.79,  "unit": "K"},
    "overall_U_assumed":   {"value": 850.0,  "unit": "W/(m²·K)"},
    "overall_U_clean":     {"value": 1020.5, "unit": "W/(m²·K)"},
    "overall_U_dirty":     {"value": 872.3,  "unit": "W/(m²·K)"},
    "area_required":       {"value": 62.8,   "unit": "m²"},
    "area_provided":       {"value": 70.5,   "unit": "m²"},
    "overdesign_pct":      12.3
  },

  "cold_side_results": {
    "mass_flow_rate": {"value": 55714.3, "unit": "kg/h"},
    "velocity":       {"value": 1.82,    "unit": "m/s"},
    "reynolds":       38450,
    "pressure_drop":  {"value": 32.4,    "unit": "kPa"},
    "heat_transfer_coeff": {"value": 5640, "unit": "W/(m²·K)"}
  },

  "hot_side_results": {
    "velocity":       {"value": 0.68,    "unit": "m/s"},
    "reynolds":       22100,
    "pressure_drop":  {"value": 45.1,    "unit": "kPa"},
    "heat_transfer_coeff": {"value": 2180, "unit": "W/(m²·K)"}
  },

  "geometry_summary": {
    "shell_id":       {"value": 489, "unit": "mm"},
    "tube_count":     196,
    "tube_length":    {"value": 6.096, "unit": "m"},
    "tube_od":        {"value": 19.05, "unit": "mm"},
    "tube_pitch":     {"value": 25.4,  "unit": "mm"},
    "baffle_spacing": {"value": 244,   "unit": "mm"},
    "baffle_count":   24,
    "num_shell_passes": 1,
    "num_tube_passes":  2
  },

  "mechanical_summary": {
    "shell_min_thickness":  {"value": 6.35,  "unit": "mm"},
    "tube_sheet_thickness": {"value": 38.1,  "unit": "mm"},
    "shell_weight_empty":   {"value": 2850,  "unit": "kg"},
    "bundle_weight":        {"value": 1920,  "unit": "kg"}
  },

  "warnings": [
    "Shell-side velocity below 0.9 m/s — fouling risk; consider reducing baffle spacing"
  ],

  "standards_references": [
    "TEMA 10th Ed. §RCB-4.4 (tube count)",
    "TEMA 10th Ed. §RCB-4.7 (baffle spacing)",
    "Kern, D.Q., Process Heat Transfer, Ch. 7 (shell-side coefficient)",
    "ASME Sec VIII Div 1 UG-27 (shell thickness)"
  ],

  "calculation_id": "uuid",
  "calc_version": "0.1.0",
  "timestamp": "2026-02-27T14:30:00Z"
}
```

#### 7.1.4 JSON Input — Rigorous Rating (`/api/v1/hx/rate`)

```json
{
  "project_id": "uuid",
  "tag": "E-101",
  "rating_mode": "check_rating",
  "hx_type": "shell_and_tube",
  "tema_type": "AES",

  "hot_side": {
    "fluid": {
      "components": [
        {"cas": "71-43-2",  "name": "Benzene",  "mole_fraction": 0.40},
        {"cas": "108-88-3", "name": "Toluene",  "mole_fraction": 0.35},
        {"cas": "106-42-3", "name": "p-Xylene", "mole_fraction": 0.25}
      ],
      "thermo_model": "PR"
    },
    "inlet_temperature":  {"value": 180.0, "unit": "°C"},
    "outlet_temperature": {"value": 80.0,  "unit": "°C"},
    "mass_flow_rate":     {"value": 30000, "unit": "kg/h"},
    "inlet_pressure":     {"value": 400,   "unit": "kPa_g"},
    "fouling_resistance": {"value": 0.000352, "unit": "m²·K/W"}
  },

  "cold_side": {
    "fluid": {
      "components": [
        {"cas": "7732-18-5", "name": "Water", "mole_fraction": 1.0}
      ],
      "thermo_model": "IAPWS97"
    },
    "inlet_temperature":  {"value": 30.0, "unit": "°C"},
    "mass_flow_rate":     {"value": 80000, "unit": "kg/h"},
    "inlet_pressure":     {"value": 500,   "unit": "kPa_g"},
    "fouling_resistance": {"value": 0.000176, "unit": "m²·K/W"}
  },

  "geometry": {
    "shell_id":         {"value": 635, "unit": "mm"},
    "tube_count":       354,
    "tube_od":          {"value": 19.05, "unit": "mm"},
    "tube_id":          {"value": 15.75, "unit": "mm"},
    "tube_length":      {"value": 4.877, "unit": "m"},
    "tube_pitch":       {"value": 25.4,  "unit": "mm"},
    "tube_layout":      "triangular_30",
    "baffle_cut":       0.25,
    "baffle_spacing":   {"value": 250, "unit": "mm"},
    "num_shell_passes": 1,
    "num_tube_passes":  4,
    "seal_strips":      1,
    "tube_to_baffle_clearance": {"value": 0.4, "unit": "mm"},
    "shell_to_baffle_clearance": {"value": 3.0, "unit": "mm"}
  },

  "method": "bell_delaware",
  "zone_analysis": true,

  "design_conditions": {
    "shell_design_pressure":    {"value": 700,  "unit": "kPa_g"},
    "tube_design_pressure":     {"value": 700,  "unit": "kPa_g"},
    "shell_design_temperature": {"value": 250,  "unit": "°C"},
    "tube_design_temperature":  {"value": 100,  "unit": "°C"},
    "shell_material": "SA-516-70",
    "tube_material":  "SA-179",
    "corrosion_allowance": {"value": 3.0, "unit": "mm"}
  },

  "output_units": "SI"
}
```

#### 7.1.5 Rating Output — Key Additional Fields

Beyond the quick-size output, the rigorous rating adds:

```json
{
  "bell_delaware_details": {
    "j_h_ideal":     0.00385,
    "j_c_baffle_cut": 1.02,
    "j_l_leakage":   0.78,
    "j_b_bypass":    0.91,
    "j_s_spacing":   0.95,
    "j_r_adverse":   1.00,
    "h_shell_corrected": {"value": 1875, "unit": "W/(m²·K)"}
  },

  "zone_analysis": [
    {
      "zone": 1,
      "zone_type": "desuperheating",
      "duty_fraction": 0.12,
      "t_hot_in": 180.0,
      "t_hot_out": 145.2,
      "t_cold_in": 48.3,
      "t_cold_out": 52.1,
      "U_zone": 420,
      "area_zone": 4.8
    },
    {
      "zone": 2,
      "zone_type": "sensible_cooling",
      "duty_fraction": 0.88,
      "t_hot_in": 145.2,
      "t_hot_out": 80.0,
      "t_cold_in": 30.0,
      "t_cold_out": 48.3,
      "U_zone": 780,
      "area_zone": 48.2
    }
  ],

  "vibration_check": {
    "natural_frequency_hz": 42.5,
    "critical_velocity_ms": 3.2,
    "actual_crossflow_velocity_ms": 1.8,
    "status": "PASS",
    "margin_pct": 43.8
  }
}
```

#### 7.1.6 Calculation Methods Implemented

| Aspect | Method | Reference |
|---|---|---|
| Tube-side HTC | Dittus-Boelter (turbulent), Sieder-Tate (viscous) | Incropera Ch. 8 |
| Shell-side HTC | Bell-Delaware (rigorous), Kern (quick) | HEDH §3.3.10, Kern Ch. 7 |
| LMTD correction F | Analytical (1-2), iterative (multi-pass) | Bowman et al., TEMA |
| Tube-side ΔP | Fanning friction + return losses | Kern Ch. 7 |
| Shell-side ΔP | Bell-Delaware stream analysis (A–E streams) | HEDH §3.3.11 |
| Vibration | Connors' criterion, acoustic resonance check | TEMA 10th Ed §V |
| Mechanical | ASME VIII Div 1 UG-27, UG-34 | ASME BPVC 2023 |

---

### 7.2 Module 12: Economic Evaluation & Industrial Utilities

#### 7.2.1 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/econ/capex/equipment` | Single equipment CAPEX estimate |
| `POST` | `/api/v1/econ/capex/project` | Total project CAPEX (Lang factor) |
| `POST` | `/api/v1/econ/opex/evaluate` | Annual OPEX breakdown |
| `POST` | `/api/v1/econ/cashflow` | NPV, IRR, payback period |
| `POST` | `/api/v1/utilities/steam` | Steam demand calculator |
| `POST` | `/api/v1/utilities/cooling-water` | CW demand and tower sizing |
| `POST` | `/api/v1/utilities/instrument-air` | IA demand and compressor sizing |
| `GET`  | `/api/v1/econ/cost-indices` | CEPCI and Nelson-Farrar history |

#### 7.2.2 JSON Input — Equipment CAPEX (`/api/v1/econ/capex/equipment`)

```json
{
  "project_id": "uuid",
  "equipment_tag": "E-101",
  "equipment_type": "shell_and_tube_hx",

  "sizing_parameters": {
    "heat_transfer_area": {"value": 70.5, "unit": "m²"},
    "design_pressure":    {"value": 1000, "unit": "kPa_g"},
    "shell_material":     "SA-516-70",
    "tube_material":      "SA-179",
    "tema_type":          "AES"
  },

  "cost_basis": {
    "method": "guthrie_bare_module",
    "base_year": 2020,
    "base_cepci": 596.2,
    "target_year": 2026,
    "target_cepci": 823.5,
    "location_factor": 1.15,
    "currency": "USD"
  },

  "overrides": {
    "base_cost_usd": null,
    "material_factor": null,
    "pressure_factor": null
  }
}
```

#### 7.2.3 JSON Output — Equipment CAPEX

```json
{
  "status": "success",
  "equipment_tag": "E-101",
  "equipment_type": "shell_and_tube_hx",

  "cost_breakdown": {
    "base_cost_2020":     {"value": 32500,  "unit": "USD", "note": "CS/CS, 150 psig base"},
    "material_factor_Fm": 1.0,
    "pressure_factor_Fp": 1.12,
    "bare_module_factor_Fbm": 3.17,
    "bare_module_cost_2020": {"value": 115668, "unit": "USD"},
    "cepci_escalation_factor": 1.381,
    "bare_module_cost_2026": {"value": 159738, "unit": "USD"},
    "location_adjusted":      {"value": 183699, "unit": "USD"}
  },

  "six_tenths_check": {
    "reference_capacity": {"value": 50.0, "unit": "m²"},
    "reference_cost":     {"value": 25000, "unit": "USD"},
    "exponent":           0.59,
    "scaled_cost":        {"value": 33210, "unit": "USD"},
    "note": "Within 2.2% of Guthrie correlation — consistent"
  },

  "method_references": [
    "Turton, R., Analysis, Synthesis and Design of Chemical Processes, 5th Ed., Ch. 7",
    "Guthrie, K.M., Chem. Eng., Mar 1969",
    "CEPCI 2026: Chemical Engineering Magazine"
  ],

  "calculation_id": "uuid",
  "timestamp": "2026-02-27T14:35:00Z"
}
```

#### 7.2.4 JSON Input — Project CAPEX (Lang Factor) (`/api/v1/econ/capex/project`)

```json
{
  "project_id": "uuid",
  "project_name": "Crude Distillation Unit Expansion",
  "plant_type": "fluid_processing",

  "equipment_list": [
    {"tag": "E-101", "bare_module_cost": 183699},
    {"tag": "E-102", "bare_module_cost": 245000},
    {"tag": "T-101", "bare_module_cost": 890000},
    {"tag": "P-101A/B", "bare_module_cost": 125000},
    {"tag": "V-101", "bare_module_cost": 310000},
    {"tag": "C-101", "bare_module_cost": 1250000}
  ],

  "lang_method": {
    "lang_factor": null,
    "use_detailed_factors": true,
    "factors": {
      "installation":       0.47,
      "instrumentation":    0.36,
      "piping":             0.68,
      "electrical":         0.11,
      "buildings":          0.18,
      "yard_improvements":  0.10,
      "service_facilities": 0.70,
      "engineering_supervision": 0.33,
      "construction":       0.41,
      "legal_fees":         0.04,
      "contractor_fee":     0.22,
      "contingency":        0.44
    }
  },

  "grassroots_extras": {
    "land":            {"value": 500000, "unit": "USD"},
    "offsite_facilities": {"value": 2000000, "unit": "USD"}
  },

  "currency": "USD",
  "cost_year": 2026
}
```

#### 7.2.5 JSON Output — Project CAPEX

```json
{
  "status": "success",
  "project_name": "Crude Distillation Unit Expansion",

  "total_bare_module_cost": {"value": 3003699, "unit": "USD"},

  "capital_cost_summary": {
    "direct_costs": {
      "purchased_equipment":    3003699,
      "installation":           1411738,
      "instrumentation":        1081332,
      "piping":                 2042516,
      "electrical":              330407,
      "subtotal_direct":        7869692
    },
    "indirect_costs": {
      "buildings":               540666,
      "yard_improvements":       300370,
      "service_facilities":     2102589,
      "engineering_supervision": 991221,
      "construction":           1231517,
      "legal_fees":              120148,
      "contractor_fee":          660814,
      "contingency":            1321628,
      "subtotal_indirect":      7268953
    },
    "fixed_capital_investment": 15138645,
    "working_capital_15pct":    2670946,
    "land":                     500000,
    "offsite_facilities":       2000000,
    "total_capital_investment": {"value": 20309591, "unit": "USD"}
  },

  "effective_lang_factor": 5.04,

  "sensitivity": {
    "capex_minus_20pct": 16247673,
    "capex_plus_20pct":  24371509,
    "contingency_range": "Class 4 estimate (±30%) per AACE 18R-97"
  },

  "calculation_id": "uuid",
  "timestamp": "2026-02-27T14:40:00Z"
}
```

#### 7.2.6 JSON Input — OPEX Evaluation (`/api/v1/econ/opex/evaluate`)

```json
{
  "project_id": "uuid",
  "annual_operating_hours": 8400,

  "raw_materials": [
    {
      "name": "Crude Oil (Arab Light)",
      "consumption_rate": {"value": 5000, "unit": "bbl/day"},
      "unit_cost": {"value": 75.0, "unit": "USD/bbl"}
    }
  ],

  "utilities": {
    "steam_hp": {
      "demand": {"value": 45000, "unit": "kg/h"},
      "unit_cost": {"value": 28.0, "unit": "USD/tonne"}
    },
    "steam_lp": {
      "demand": {"value": 22000, "unit": "kg/h"},
      "unit_cost": {"value": 15.0, "unit": "USD/tonne"}
    },
    "cooling_water": {
      "demand": {"value": 3500, "unit": "m³/h"},
      "unit_cost": {"value": 0.05, "unit": "USD/m³"}
    },
    "electricity": {
      "demand": {"value": 8500, "unit": "kW"},
      "unit_cost": {"value": 0.08, "unit": "USD/kWh"}
    },
    "fuel_gas": {
      "demand": {"value": 2000, "unit": "kg/h"},
      "unit_cost": {"value": 0.35, "unit": "USD/kg"}
    }
  },

  "labor": {
    "operators_per_shift": 6,
    "shifts_per_day":      4,
    "annual_salary_usd":   85000,
    "overhead_factor":     1.6
  },

  "maintenance": {
    "method": "percentage_of_fci",
    "fci_usd": 15138645,
    "percentage": 0.06
  },

  "insurance_and_taxes": {
    "method": "percentage_of_fci",
    "percentage": 0.03
  },

  "depreciation": {
    "method": "straight_line",
    "depreciable_capital": 15138645,
    "salvage_value": 1500000,
    "useful_life_years": 20
  },

  "currency": "USD"
}
```

#### 7.2.7 JSON Output — OPEX

```json
{
  "status": "success",
  "annual_operating_hours": 8400,

  "opex_breakdown": {
    "raw_materials":    {"value": 136875000, "unit": "USD/yr"},
    "utilities": {
      "steam_hp":       {"value": 10584000, "unit": "USD/yr"},
      "steam_lp":       {"value": 2772000,  "unit": "USD/yr"},
      "cooling_water":  {"value": 1470000,  "unit": "USD/yr"},
      "electricity":    {"value": 5712000,  "unit": "USD/yr"},
      "fuel_gas":       {"value": 5880000,  "unit": "USD/yr"},
      "subtotal_util":  {"value": 26418000, "unit": "USD/yr"}
    },
    "labor": {
      "operating_labor":    {"value": 2040000, "unit": "USD/yr"},
      "with_overhead":      {"value": 3264000, "unit": "USD/yr"}
    },
    "maintenance":          {"value": 908319,  "unit": "USD/yr"},
    "insurance_and_taxes":  {"value": 454160,  "unit": "USD/yr"},
    "depreciation":         {"value": 681932,  "unit": "USD/yr"},

    "total_opex":           {"value": 168601411, "unit": "USD/yr"}
  },

  "unit_cost_of_production": {
    "per_barrel_crude": {"value": 92.27, "unit": "USD/bbl"},
    "note": "Includes all fixed + variable costs"
  },

  "calculation_id": "uuid",
  "timestamp": "2026-02-27T14:45:00Z"
}
```

#### 7.2.8 Utilities Calculator — Steam Demand (`/api/v1/utilities/steam`)

```json
// INPUT
{
  "consumers": [
    {
      "tag": "E-101",
      "duty_kw": 3488.9,
      "steam_pressure": "HP",
      "steam_conditions": {
        "pressure": {"value": 4200, "unit": "kPa_a"},
        "superheat": {"value": 50, "unit": "°C"}
      }
    },
    {
      "tag": "E-105 (Reboiler)",
      "duty_kw": 12500,
      "steam_pressure": "LP",
      "steam_conditions": {
        "pressure": {"value": 450, "unit": "kPa_a"},
        "superheat": {"value": 0, "unit": "°C"}
      }
    }
  ],
  "condensate_return_pct": 85,
  "bfw_temperature": {"value": 105, "unit": "°C"}
}

// OUTPUT
{
  "steam_summary": [
    {
      "header": "HP",
      "total_duty_kw": 3488.9,
      "latent_heat_kj_kg": 1714.5,
      "mass_flow_kg_h": 7324.1,
      "consumers": ["E-101"]
    },
    {
      "header": "LP",
      "total_duty_kw": 12500,
      "latent_heat_kj_kg": 2113.2,
      "mass_flow_kg_h": 21296.3,
      "consumers": ["E-105 (Reboiler)"]
    }
  ],
  "total_steam_demand_kg_h": 28620.4,
  "makeup_water_kg_h": 4293.1,
  "bfw_preheat_duty_kw": 502.3
}
```

---

## 8. Cross-Cutting Concerns

### 8.1 Unit Conversion

A central `UnitRegistry` (built on `pint`) handles all conversions. Every
numeric value in the system is stored as a `(magnitude, unit)` pair. The
kernel operates exclusively in SI; conversion happens at the boundary.

### 8.2 Standards Traceability

Every module function is decorated with its standards reference:

```python
@standards_ref("API 520 Part I, §4.3.2", "ASME Sec VIII Div 1, UG-125")
def size_gas_psv(W, T, Z, M, k, P1, Kb, Kc, Kd) -> PSVResult:
    ...
```

The decorator registers the reference in the audit trail automatically.

### 8.3 Error Handling Strategy

| Error Class | HTTP Code | Behavior |
|---|---|---|
| `ValidationError` (Pydantic) | 422 | Return field-level errors |
| `ThermodynamicConvergenceError` | 422 | Return last iteration state + suggestion |
| `ComponentNotFoundError` | 404 | Suggest closest CAS match |
| `StandardsViolationWarning` | 200 | Return result with `warnings[]` array |
| `CalculationTimeout` | 504 | Kill Celery task, return partial results |

### 8.4 Testing Strategy

| Level | Tool | Coverage Target |
|---|---|---|
| Unit (kernel functions) | pytest + hypothesis | 95% line coverage |
| Integration (API → DB) | pytest + httpx.AsyncClient | All endpoints |
| Property validation | pytest vs. NIST WebBook data | ≤ 1% deviation on 100 compounds |
| Regression | Golden-file tests (input JSON → expected output JSON) | All modules |
| E2E (UI) | Playwright | Critical user flows |

### 8.5 Security

- All inputs sanitized via Pydantic (no raw SQL, no eval).
- RBAC: Viewer → Editor → Approver → Admin roles.
- Project-level isolation (row-level security in PostgreSQL).
- Calculation inputs/outputs encrypted at rest (AES-256).
- SOC 2 Type II audit trail via `calculation_audit` table.

---

## 9. Appendices

### Appendix A — TEMA Type Code Reference

| Position | Options | Meaning |
|---|---|---|
| Front head | A, B, C, N, D | Type of front-end stationary head |
| Shell | E, F, G, H, J, K, X | Shell type |
| Rear head | L, M, N, P, S, T, U, W | Type of rear-end head |

Common configurations: AES (most common), BEM (fixed tubesheet), AKT (kettle reboiler), AEP (floating head).

### Appendix B — Cost Index Reference

| Year | CEPCI | Nelson-Farrar |
|---|---|---|
| 2000 | 394.1 | 1542 |
| 2005 | 468.2 | 1918 |
| 2010 | 550.8 | 2269 |
| 2015 | 556.8 | 2352 |
| 2020 | 596.2 | 2478 |
| 2024 | 790.1 | 3102 |
| 2026 | 823.5 (est.) | 3250 (est.) |

### Appendix C — Abbreviations

| Abbrev. | Meaning |
|---|---|
| ASME | American Society of Mechanical Engineers |
| API | American Petroleum Institute |
| TEMA | Tubular Exchanger Manufacturers Association |
| ISA | International Society of Automation |
| PIP | Process Industry Practices |
| CEPCI | Chemical Engineering Plant Cost Index |
| EOS | Equation of State |
| VLE | Vapor-Liquid Equilibrium |
| LMTD | Log Mean Temperature Difference |
| HTC | Heat Transfer Coefficient |
| PSV | Pressure Safety Valve |
| PRV | Pressure Relief Valve |
| NPSH | Net Positive Suction Head |
| HAZOP | Hazard and Operability Study |
| LOPA | Layer of Protection Analysis |
| MPC | Model Predictive Control |
| APC | Advanced Process Control |
| CAPEX | Capital Expenditure |
| OPEX | Operating Expenditure |
| FCI | Fixed Capital Investment |
| TCI | Total Capital Investment |
| NPV | Net Present Value |
| IRR | Internal Rate of Return |
