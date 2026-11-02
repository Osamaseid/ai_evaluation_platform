import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';

describe('ApiClient Unit Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    api.setToken(null);
    vi.restoreAllMocks();
  });

  it('manages bearer authentication token in memory and localStorage', () => {
    expect(api.getToken()).toBeNull();

    api.setToken('test-signed-jwt-token');
    expect(api.getToken()).toBe('test-signed-jwt-token');
    expect(localStorage.getItem('autograde_token')).toBe('test-signed-jwt-token');

    api.setToken(null);
    expect(api.getToken()).toBeNull();
    expect(localStorage.getItem('autograde_token')).toBeNull();
  });

  it('attaches Authorization header when token is present', async () => {
    api.setToken('secret-bearer-token');

    const fakeResponse = {
      user_id: 'student_ada',
      name: 'Ada Lovelace',
      email: 'ada@university.edu',
      role: 'student',
      is_active: true,
      created_at: '2026-11-01T00:00:00Z',
    };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => fakeResponse,
    } as Response);

    const user = await api.getCurrentUser();
    expect(user.user_id).toBe('student_ada');
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    const calledHeaders = fetchSpy.mock.calls[0][1]?.headers as Headers;
    expect(calledHeaders.get('Authorization')).toBe('Bearer secret-bearer-token');
  });

  it('extracts API error message from error envelope on 400/409', async () => {
    const errorPayload = {
      error: {
        code: 'DUPLICATE_ENTITY',
        message: 'Student account already registered with this email',
        status_code: 409,
      },
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 409,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => errorPayload,
    } as Response);

    await expect(
      api.register({
        user_id: 'student_dup',
        name: 'Duplicate Student',
        email: 'dup@university.edu',
        password: 'pass',
        role: 'student',
      })
    ).rejects.toThrow('Student account already registered with this email');
  });

  it('handles 204 No Content gracefully', async () => {
    api.setToken('token-to-revoke');

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 204,
      headers: new Headers(),
    } as Response);

    await api.logout();
    expect(api.getToken()).toBeNull();
  });
});

