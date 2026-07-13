import { api } from "@/lib/api";
import type { User } from "@/types/auth";

export const profileService = {
  async update(data: Partial<Pick<User, "full_name">>): Promise<User> {
    const res = await api.put("/auth/me", data);
    return res.data;
  },

  async updatePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const res = await api.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return res.data;
  },
};
