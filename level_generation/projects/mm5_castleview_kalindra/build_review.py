"""Rebuild source census, occupancy evidence, wireframes, documents and focused layout checks."""
import audit_occupancy
import build_plan
import enrich_plan
import map_architecture
import build_landscape
import render_review
import validate_plan

audit_occupancy.build()
build_plan.build()
enrich_plan.build()
map_architecture.build()
build_landscape.build()
validate_plan.build()
render_review.build()
