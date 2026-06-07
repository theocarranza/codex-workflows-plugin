# Date and Time Handling

## I. Immutability of UTC Data

1. **Preserve Original Dates.** Treat all incoming ISO UTC strings (`startDateTime`, `startedAt`) as immutable. Never mutate the document body timestamp to account for a local timezone.

## II. explicit Timezone Bucketing

1. **Reject Local Timezone Implicit Conversions.** **Do not** use `date-fns` default format functions (like `convertDateToDateOnly`) for document ID generation or comparisons. These depend on the physical server's timezone, causing severe bugs between emulators (UTC-3) and production (UTC).
2. **Mandatory Reference Helpers.** All date-to-string bucket evaluations **must** explicitly enforce the target timezone (typically `America/Sao_Paulo`).
3. **Approved Functions:** You must only use robust helpers strictly pointing to `date-fns-tz` such as `getDayAsReference(date)` and `getMonthAsReference(date)` from `projects/functions/src/helpers/date-helpers.ts`.

## III. Application Example

When creating a day bucket ID:

```typescript
import { getDayAsReference } from "../../../helpers/date-helpers";
const dayBucketId = getDayAsReference(new Date(event.startDateTime)); // ✅ Correct
```
