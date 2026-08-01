# gc-326 Interface Contract — MealMaster (MARBLE coding task_id=51)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=51, at commit
`8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-326/solution.py`.

A recipe is a dict with keys: `name` (unique str), `meal_type` in
`{"breakfast","lunch","dinner","snack"}`, `tags` (list[str]), `allergens` (list[str]),
`calories`, `protein`, `carbs`, `fat`, `fiber` (ints), `ingredients` (list[str]),
`instructions` (str).

## class MealMaster(recipes: list[dict])

- Constructor raises `ValueError` if any recipe has an invalid `meal_type`.
- `set_profile(user, preferences, allergies, goal, daily_calories) -> None`
  - `goal` in `{"weight_loss","muscle_gain","maintenance"}` else `ValueError`;
    `daily_calories <= 0` raises `ValueError`. Re-setting replaces the profile.
- `candidates(user, meal_type) -> list[str]` — sorted names of recipes of that
  `meal_type` whose `tags` contain every entry of the user's `preferences` and whose
  `allergens` share nothing with the user's `allergies`. Unknown user raises `KeyError`.
- `generate_week_plan(user, tolerance=0.2) -> dict` — keys `"day1"`..`"day7"`, each a
  dict with keys `breakfast, lunch, dinner, snack` mapping to recipe names. Every
  chosen recipe must be a valid candidate for its slot, and each day's calorie total
  must lie within `[daily_calories*(1-tolerance), daily_calories*(1+tolerance)]`.
  Raises `RuntimeError` if no valid plan exists. The plan is stored for the user.
- `day_nutrition(user, day) -> dict` — sums `calories, protein, carbs, fat, fiber`
  over the stored plan for `day` (e.g. `"day3"`). Raises `RuntimeError` if no plan
  has been generated for the user.
- `swap(user, day, meal_type, recipe_name) -> None` — replaces one slot in the stored
  plan. Unknown recipe raises `KeyError`; a recipe that is the wrong `meal_type`,
  violates preferences/allergies, or pushes the day outside the calorie tolerance used
  at generation time raises `ValueError`.
