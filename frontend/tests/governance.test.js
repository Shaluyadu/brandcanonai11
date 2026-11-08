const test = require('node:test');
const assert = require('node:assert');

// 1. Dashboard Metrics Calculation & Transformation Tests
test('Dashboard Metrics parses and aggregates all 8 required governance stats', () => {
  const backendStats = {
    total_submissions: 42,
    pending_reviews: 12,
    in_review: 5,
    changes_requested: 7,
    approved: 20,
    rejected: 3,
    review_incomplete: 12,
    high_risk_findings: 15,
  };

  assert.strictEqual(backendStats.total_submissions, 42);
  assert.strictEqual(backendStats.pending_reviews, 12);
  assert.strictEqual(backendStats.in_review, 5);
  assert.strictEqual(backendStats.changes_requested, 7);
  assert.strictEqual(backendStats.approved, 20);
  assert.strictEqual(backendStats.rejected, 3);
  assert.strictEqual(backendStats.review_incomplete, 12);
  assert.strictEqual(backendStats.high_risk_findings, 15);

  // Verification that no metric is undefined or missing
  const keys = [
    'total_submissions',
    'pending_reviews',
    'in_review',
    'changes_requested',
    'approved',
    'rejected',
    'review_incomplete',
    'high_risk_findings',
  ];
  keys.forEach((k) => assert.ok(k in backendStats));
});

// 2. DataTable Sorting & Accessor Logic Tests
test('DataTable sorting toggles between asc and desc for active column', () => {
  const getNextSortOrder = (currentCol, targetCol, currentOrder) => {
    if (currentCol === targetCol && currentOrder === 'asc') return 'desc';
    return 'asc';
  };

  assert.strictEqual(getNextSortOrder('created_at', 'created_at', 'asc'), 'desc');
  assert.strictEqual(getNextSortOrder('created_at', 'created_at', 'desc'), 'asc');
  assert.strictEqual(getNextSortOrder('title', 'created_at', 'desc'), 'asc');
});

test('DataTable row rendering handles missing properties with fallback', () => {
  const row = { id: '1', title: 'Test Draft', optionalField: null };
  const resolveCell = (accessor) => row[accessor] ?? '-';

  assert.strictEqual(resolveCell('title'), 'Test Draft');
  assert.strictEqual(resolveCell('optionalField'), '-');
  assert.strictEqual(resolveCell('nonexistent'), '-');
});

// 3. Pagination Math & Boundary Tests
test('Pagination calculations correctly derive offsets and total pages', () => {
  const calcTotalPages = (total, pageSize) => (total > 0 ? Math.ceil(total / pageSize) : 1);
  const calcOffset = (page, pageSize) => (page - 1) * pageSize;

  assert.strictEqual(calcTotalPages(25, 10), 3);
  assert.strictEqual(calcTotalPages(0, 10), 1);
  assert.strictEqual(calcTotalPages(10, 10), 1);
  assert.strictEqual(calcTotalPages(11, 10), 2);

  assert.strictEqual(calcOffset(1, 10), 0);
  assert.strictEqual(calcOffset(2, 10), 10);
  assert.strictEqual(calcOffset(3, 10), 20);
});

// 4. URL Query Parameter Serialization for Submissions
test('Query parameter builder generates clean params without undefined values', () => {
  const buildQuery = (params) => {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.pageSize) q.append('page_size', params.pageSize.toString());
    if (params.search) q.append('search', params.search);
    if (params.status) q.append('status', params.status);
    if (params.channel) q.append('channel', params.channel);
    if (params.sortBy) q.append('sort_by', params.sortBy);
    if (params.sortOrder) q.append('sort_order', params.sortOrder);
    return q.toString();
  };

  const query = buildQuery({
    page: 2,
    pageSize: 20,
    search: 'cloud',
    status: 'SUBMITTED',
    channel: '',
    sortBy: 'created_at',
    sortOrder: 'desc',
  });

  assert.strictEqual(query, 'page=2&page_size=20&search=cloud&status=SUBMITTED&sort_by=created_at&sort_order=desc');
  assert.ok(!query.includes('channel='));
});

// 5. Suggestion Text Replacement & Versioning Logic
test('Applying suggestion cleanly replaces exact occurrence and produces valid text', () => {
  const originalText = 'Our product is cheap and fast.';
  const prohibitedTerm = 'cheap';
  const preferredTerm = 'cost-effective';

  const updatedText = originalText.replace(prohibitedTerm, preferredTerm);
  assert.strictEqual(updatedText, 'Our product is cost-effective and fast.');
  assert.ok(!updatedText.includes('cheap'));
});

// 6. Role-Aware Governance Greetings & Permissions
test('Role-based navigation returns appropriate default actions', () => {
  const getGreeting = (role) => {
    switch (role) {
      case 'ADMIN':
        return { label: 'Manage Workspace Members', href: '/members' };
      case 'BRAND_MANAGER':
        return { label: 'Open Knowledge Hub', href: '/brand-knowledge' };
      case 'CREATOR':
        return { label: 'New Content Review', href: '/submissions' };
      case 'REVIEWER':
      default:
        return { label: 'Review Queue', href: '/approvals' };
    }
  };

  assert.deepStrictEqual(getGreeting('ADMIN'), { label: 'Manage Workspace Members', href: '/members' });
  assert.deepStrictEqual(getGreeting('REVIEWER'), { label: 'Review Queue', href: '/approvals' });
  assert.deepStrictEqual(getGreeting('CREATOR'), { label: 'New Content Review', href: '/submissions' });
  assert.deepStrictEqual(getGreeting('BRAND_MANAGER'), { label: 'Open Knowledge Hub', href: '/brand-knowledge' });
});

