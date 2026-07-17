use crate::wire::{PhaseClientDelta, PhaseClientDeltaOp};
use serde_json::Value;

pub(crate) fn phase_delta(previous: &Value, current: &Value) -> PhaseClientDelta {
    fn walk(
        path: &mut Vec<String>,
        previous: &Value,
        current: &Value,
        ops: &mut Vec<PhaseClientDeltaOp>,
    ) {
        if previous == current {
            return;
        }
        if let (Some(before), Some(after)) = (previous.as_object(), current.as_object()) {
            for key in before.keys().filter(|key| !after.contains_key(*key)) {
                path.push(key.clone());
                ops.push(PhaseClientDeltaOp::Remove { path: path.clone() });
                path.pop();
            }
            for (key, value) in after {
                path.push(key.clone());
                match before.get(key) {
                    Some(old) => walk(path, old, value, ops),
                    None => ops.push(PhaseClientDeltaOp::Set {
                        path: path.clone(),
                        value: value.clone(),
                    }),
                }
                path.pop();
            }
        } else {
            ops.push(PhaseClientDeltaOp::Set {
                path: path.clone(),
                value: current.clone(),
            });
        }
    }

    let mut ops = Vec::new();
    walk(&mut Vec::new(), previous, current, &mut ops);
    PhaseClientDelta { ops }
}

pub(crate) fn apply_phase_delta(target: &mut Value, delta: &PhaseClientDelta) {
    fn set_path(target: &mut Value, path: &[String], value: Value) {
        if path.is_empty() {
            *target = value;
            return;
        }
        if !target.is_object() {
            *target = Value::Object(Default::default());
        }
        let object = target.as_object_mut().expect("object created above");
        if path.len() == 1 {
            object.insert(path[0].clone(), value);
        } else {
            set_path(
                object
                    .entry(path[0].clone())
                    .or_insert_with(|| Value::Object(Default::default())),
                &path[1..],
                value,
            );
        }
    }

    fn remove_path(target: &mut Value, path: &[String]) {
        let Some(object) = target.as_object_mut() else {
            return;
        };
        if path.len() == 1 {
            object.remove(&path[0]);
        } else if let Some(child) = object.get_mut(&path[0]) {
            remove_path(child, &path[1..]);
        }
    }

    for op in &delta.ops {
        match op {
            PhaseClientDeltaOp::Set { path, value } => set_path(target, path, value.clone()),
            PhaseClientDeltaOp::Remove { path } if !path.is_empty() => remove_path(target, path),
            PhaseClientDeltaOp::Remove { .. } => *target = Value::Null,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_nested_state() {
        let previous = serde_json::json!({
            "state": {"objects": {"1": {"name": "Bear", "tapped": false}}, "gone": 1},
            "legal_actions": []
        });
        let current = serde_json::json!({
            "state": {"objects": {"1": {"name": "Bear", "tapped": true}, "2": null}},
            "legal_actions": [{"type": "PassPriority"}]
        });
        let delta = phase_delta(&previous, &current);
        let mut restored = previous;
        apply_phase_delta(&mut restored, &delta);
        assert_eq!(restored, current);
    }
}
