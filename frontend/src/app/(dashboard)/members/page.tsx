"use client";

import React, { useEffect, useState } from "react";
import {
  Users,
  UserPlus,
  Shield,
  Trash2,
  AlertCircle,
  CheckCircle2,
  X,
  Mail,
  User as UserIcon,
  ShieldAlert
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { Member } from "@/types/member";
import { RoleType } from "@/types/auth";
import { formatDate } from "@/lib/utils";

export default function MembersPage() {
  const { user: currentUser, activeOrganisation, isAdmin } = useAuth();
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState<RoleType>("CREATOR");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchMembers = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.members.list(1, 100);
      if (res.success && res.data) {
        setMembers(res.data.items);
      } else {
        setErrorMessage(res.error?.message || "Failed to load members");
      }
    } catch {
      setErrorMessage("Network error loading members");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [activeOrganisation]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail || !inviteName) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const res = await api.members.invite({
      email: inviteEmail,
      full_name: inviteName,
      role: inviteRole,
    });

    setIsSubmitting(false);

    if (res.success) {
      setSuccessMessage(`Successfully added ${inviteEmail} with role ${inviteRole}`);
      setShowInviteModal(false);
      setInviteEmail("");
      setInviteName("");
      setInviteRole("CREATOR");
      fetchMembers();
    } else {
      setErrorMessage(res.error?.message || "Failed to add member");
    }
  };

  const handleRoleChange = async (memberId: string, newRole: RoleType) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    const res = await api.members.updateRole(memberId, newRole);
    if (res.success) {
      setSuccessMessage("Member role updated successfully");
      fetchMembers();
    } else {
      setErrorMessage(res.error?.message || "Failed to update role");
    }
  };

  const handleRemoveMember = async (memberId: string, memberEmail: string) => {
    if (!confirm(`Are you sure you want to remove ${memberEmail} from this workspace?`)) return;

    setErrorMessage(null);
    setSuccessMessage(null);
    const res = await api.members.remove(memberId);
    if (res.success) {
      setSuccessMessage(`Removed ${memberEmail} from workspace`);
      fetchMembers();
    } else {
      setErrorMessage(res.error?.message || "Failed to remove member");
    }
  };

  const getRoleBadgeStyle = (role: RoleType) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "BRAND_MANAGER":
        return "bg-orange-50 text-orange-700 border-orange-200";
      case "CREATOR":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "REVIEWER":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
    }
  };

  return (
    <div>
      <Header
        title="Members & Roles"
        description="Manage workspace team members and assign role-based access permissions."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Banner for Non-Admins */}
        {!isAdmin && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3 text-xs text-amber-800">
            <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
            <div>
              <span className="font-semibold">Read-Only View:</span> Only Workspace Admins have authority to invite members, modify roles, or remove members from this workspace.
            </div>
          </div>
        )}

        {/* Feedback alerts */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-between text-xs text-rose-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-700">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Actions Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <Users className="w-4 h-4 text-slate-400" />
            <span>Total Members: {members.length}</span>
          </div>

          {isAdmin && (
            <button
              onClick={() => setShowInviteModal(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs shadow-brand-600/30 transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              <span>Invite New Member</span>
            </button>
          )}
        </div>

        {/* Members Table */}
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-6">Member</th>
                <th className="py-3 px-6">Assigned Role</th>
                <th className="py-3 px-6">Date Added</th>
                {isAdmin && <th className="py-3 px-6 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {isLoading ? (
                <tr>
                  <td colSpan={isAdmin ? 4 : 3} className="py-8 text-center text-slate-400">
                    Loading members...
                  </td>
                </tr>
              ) : members.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 4 : 3} className="py-8 text-center text-slate-400">
                    No members found in this workspace.
                  </td>
                </tr>
              ) : (
                members.map((member) => {
                  const isCurrent = member.user_id === currentUser?.id;
                  return (
                    <tr key={member.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                            {member.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                              <span>{member.full_name}</span>
                              {isCurrent && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-normal">
                                  You
                                </span>
                              )}
                            </div>
                            <div className="text-slate-500 text-[11px]">{member.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-6">
                        {isAdmin ? (
                          <select
                            value={member.role}
                            onChange={(e) => handleRoleChange(member.id, e.target.value as RoleType)}
                            className="px-2 py-1 rounded border border-slate-200 text-xs font-semibold bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
                          >
                            <option value="ADMIN">ADMIN</option>
                            <option value="BRAND_MANAGER">BRAND_MANAGER</option>
                            <option value="CREATOR">CREATOR</option>
                            <option value="REVIEWER">REVIEWER</option>
                          </select>
                        ) : (
                          <span
                            className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border ${getRoleBadgeStyle(
                              member.role
                            )}`}
                          >
                            {member.role.replace("_", " ")}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-6 text-slate-500">{formatDate(member.created_at)}</td>
                      {isAdmin && (
                        <td className="py-3.5 px-6 text-right">
                          <button
                            onClick={() => handleRemoveMember(member.id, member.email)}
                            title="Remove Member"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-brand-600" />
                <h3 className="text-base font-bold text-slate-900">Add Workspace Member</h3>
              </div>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="e.g. Jordan Smith"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Work Email</label>
                <input
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="jordan@company.com"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assigned Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as RoleType)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500"
                >
                  <option value="CREATOR">Content Creator (Drafts & reviews content)</option>
                  <option value="REVIEWER">Reviewer (Audits & approves submissions)</option>
                  <option value="BRAND_MANAGER">Brand Manager (Governs guidelines & facts)</option>
                  <option value="ADMIN">Workspace Admin (Full workspace governance)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Adding..." : "Add Member"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

