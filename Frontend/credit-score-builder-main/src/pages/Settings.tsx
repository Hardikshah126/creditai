import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";
import { getUser, updateProfile } from "@/lib/api";
import { toast } from "sonner";

const SettingsPage = () => {
  const user = getUser();
  const [name, setName] = useState(user?.name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateProfile({ name, phone });
      // Update localStorage too
      const stored = localStorage.getItem("user");
      if (stored) {
        const parsed = JSON.parse(stored);
        localStorage.setItem("user", JSON.stringify({ ...parsed, name, phone }));
      }
      toast.success("Settings saved!");
    } catch (err: any) {
      toast.error(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadData = () => {
    const data = {
      user,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "creditai-my-data.json";
    a.click();
    toast.success("Data downloaded!");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Settings</h2>
        <p className="text-muted-foreground mt-1">Manage your profile and preferences.</p>
      </div>

      <Card className="p-6 space-y-4">
        <h3 className="font-semibold text-foreground">Personal Information</h3>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="s-name">Full Name</Label>
            <Input
              id="s-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="s-phone">Phone Number</Label>
            <Input
              id="s-phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="s-country">Country</Label>
            <Input
              id="s-country"
              value={user?.country || "India"}
              disabled
              className="mt-1 bg-muted"
            />
          </div>
          <div>
            <Label htmlFor="s-email">Email</Label>
            <Input
              id="s-email"
              value={user?.email || ""}
              disabled
              className="mt-1 bg-muted"
            />
          </div>
        </div>
        <Button className="rounded-lg" onClick={handleSave} disabled={saving}>
          {saving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</> : "Save Changes"}
        </Button>
      </Card>

      <Card className="p-6 space-y-4">
        <h3 className="font-semibold text-foreground">Data & Privacy</h3>
        <p className="text-sm text-muted-foreground">
          Your data is encrypted and never sold to third parties. All financial documents
          are processed securely and stored with bank-grade encryption.
        </p>
        <Separator />
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" className="rounded-lg" onClick={handleDownloadData}>
            Download My Data
          </Button>
          <Button
            variant="outline"
            className="rounded-lg text-destructive border-destructive/30 hover:bg-destructive/10"
            onClick={() => toast.error("Please contact support to delete your account.")}
          >
            Delete Account
          </Button>
        </div>
      </Card>

      <Card className="p-6 space-y-2">
        <h3 className="font-semibold text-foreground">Account Info</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>Role: <span className="text-foreground capitalize">{user?.role || "applicant"}</span></p>
          <p>Member since: <span className="text-foreground">
            {user?.created_at ? new Date(user.created_at).toLocaleDateString("en-IN", { month: "long", year: "numeric" }) : "—"}
          </span></p>
        </div>
      </Card>
    </div>
  );
};

export default SettingsPage;